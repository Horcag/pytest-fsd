"""Inspect programmatic imports with a bounded, non-executing AST evaluator."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .ast_utils import get_node_location
from .violations import Violation

UNKNOWN = object()
MAX_TEXT = 65536
MAX_CODE_DEPTH = 8


@dataclass(frozen=True)
class Symbol:
    name: str


@dataclass(frozen=True)
class Code:
    source: str
    mode: str


@dataclass
class ImportAnalysis:
    imports: List[ast.AST] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)


BUILTINS = {name: Symbol('builtins.' + name) for name in (
    '__import__', 'exec', 'eval', 'compile', 'globals', 'locals', 'getattr',
)}
LOADERS = {'importlib.import_module', 'importlib.__import__', 'builtins.__import__'}


def analyze_imports(source: str, tree: ast.AST, file_path: str, base_dir: str) -> ImportAnalysis:
    """Resolve known dynamic imports; report recognized calls that remain unknown."""
    package = '.'.join((Path(base_dir).name,) + Path(file_path).relative_to(base_dir).parent.parts)
    analyzer = _Analyzer(source, file_path, package)
    try:
        analyzer.visit(tree)
    except RecursionError:
        analyzer.error(tree, 'Analysis exceeded the AST nesting limit')
    return analyzer.result


class _Analyzer(ast.NodeVisitor):
    def __init__(self, source, file_path, package):
        self.source = source
        self.file_path = file_path
        self.env: Dict[str, object] = {'__package__': package, '__builtins__': Symbol('builtins')}
        self.result = ImportAnalysis()
        self.origin = None
        self.depth = 0
        self.code_expansions = 0
        self.code_bytes = 0
        self.class_parent = None

    def error(self, node, message):
        if len(self.result.violations) >= 64:
            return
        node = self.origin if self.origin is not None else node
        self.result.violations.append(Violation(
            rule='dynamic-imports', file_path=self.file_path,
            message=message + '. Use an explicit import or a statically resolvable target.',
            **get_node_location(node, self.source),
        ))

    def record(self, node):
        if self.origin is not None:
            ast.copy_location(node, self.origin)
        self.result.imports.append(node)

    def lookup(self, name):
        return self.env.get(name, BUILTINS.get(name, UNKNOWN))

    def bind(self, target, value=UNKNOWN):
        if isinstance(target, ast.Name):
            self.env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            values = value if isinstance(value, (tuple, list)) and len(value) == len(target.elts) else [UNKNOWN] * len(target.elts)
            for child, item in zip(target.elts, values):
                self.bind(child, item)
        else:
            # Mutating containers invalidates any previously inferred contents.
            root = target
            while isinstance(root, (ast.Subscript, ast.Attribute)):
                root = root.value
            if isinstance(root, ast.Name):
                self.env[root.id] = UNKNOWN

    def visit_Import(self, node):
        self.record(node)
        for alias in node.names:
            self.env[alias.asname or alias.name.split('.')[0]] = Symbol(alias.name if alias.asname else alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        self.record(node)
        for alias in node.names:
            if alias.name == '*' and not node.level and node.module == 'importlib':
                self.env.update({name: Symbol('importlib.' + name) for name in ('import_module', '__import__')})
                continue
            self.env[alias.asname or alias.name] = Symbol((node.module or '') + '.' + alias.name) if not node.level else UNKNOWN

    def visit_Assign(self, node):
        value = self.expr(node.value)
        for target in node.targets:
            self.bind(target, value)

    def visit_AnnAssign(self, node):
        self.expr(node.annotation)
        self.bind(node.target, self.expr(node.value) if node.value else UNKNOWN)

    def visit_AugAssign(self, node):
        left, right = self.expr(node.target), self.expr(node.value)
        value = self.add(left, right) if isinstance(node.op, ast.Add) else UNKNOWN
        self.bind(node.target, value)

    def visit_Delete(self, node):
        for target in node.targets:
            self.bind(target)

    def visit_Expr(self, node):
        self.expr(node.value)

    def visit_Call(self, node):
        self.expr(node)

    def visit_NamedExpr(self, node):
        self.expr(node)

    def visit_Lambda(self, node):
        self.expr(node)

    def scoped(self, node):
        for item in getattr(node, 'decorator_list', []):
            self.expr(item)
        args = getattr(node, 'args', None)
        if args:
            default_loaders = self.default_loaders(args)
            for arg in args.posonlyargs + args.args + args.kwonlyargs + [a for a in (args.vararg, args.kwarg) if a is not None]:
                self.expr(arg.annotation)
            self.expr(getattr(node, 'returns', None))
        else:
            for value in getattr(node, 'bases', []):
                self.expr(value)
            for keyword in getattr(node, 'keywords', []):
                self.expr(keyword.value)
        self.env[node.name] = UNKNOWN
        outer = self.env
        previous_class_parent = self.class_parent
        if isinstance(node, ast.ClassDef):
            self.class_parent = self.class_parent if self.class_parent is not None else outer
            self.env = dict(outer)
        else:
            self.env = dict(self.class_parent if self.class_parent is not None else outer)
            self.class_parent = None
        # Python binds locals for the entire function, including before assignment.
        if args:
            for name in _local_names(node):
                self.env[name] = UNKNOWN
            for name in default_loaders:
                self.env[name] = Symbol('?dynamic')
        for statement in node.body:
            self.visit(statement)
        self.env = outer
        self.class_parent = previous_class_parent

    visit_FunctionDef = scoped
    visit_AsyncFunctionDef = scoped
    visit_ClassDef = scoped

    def visit_If(self, node):
        self.expr(node.test)
        self.branches([node.body, node.orelse])

    def branches(self, blocks):
        before = dict(self.env)
        outcomes = []
        for block in blocks:
            self.env = dict(before)
            for statement in block:
                self.visit(statement)
            outcomes.append(self.env)
        self.env = self.merge(outcomes)

    def visit_For(self, node):
        self.expr(node.iter)
        self.bind(node.target)
        self.branches([node.body + node.orelse, []])

    visit_AsyncFor = visit_For

    def visit_While(self, node):
        self.expr(node.test)
        self.branches([node.body + node.orelse, []])

    def visit_Try(self, node):
        # Inspect every path; uncertain bindings remain unknown after the join.
        blocks = [node.body + node.orelse]
        for handler in node.handlers:
            self.expr(handler.type)
            block = list(handler.body)
            if handler.name:
                block.insert(0, ast.Assign(targets=[ast.Name(id=handler.name, ctx=ast.Store())], value=ast.Constant(value=None)))
            blocks.append(block)
        self.branches(blocks)
        for statement in node.finalbody:
            self.visit(statement)

    def visit_With(self, node):
        for item in node.items:
            self.expr(item.context_expr)
            if item.optional_vars:
                self.bind(item.optional_vars)
        for statement in node.body:
            self.visit(statement)

    visit_AsyncWith = visit_With

    def add(self, left, right):
        if isinstance(left, str) and isinstance(right, str) and len(left) + len(right) <= MAX_TEXT:
            return left + right
        if isinstance(left, (tuple, list)) and type(left) is type(right) and len(left) + len(right) <= 256:
            return left + right
        return UNKNOWN

    def expr(self, node):
        if node is None:
            return UNKNOWN
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.lookup(node.id)
        if isinstance(node, ast.Attribute):
            value = self.expr(node.value)
            if isinstance(value, Symbol):
                return Symbol(value.name + '.' + node.attr)
            return Symbol('?dynamic') if _may_load(value) else UNKNOWN
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return tuple(self.expr(item) for item in node.elts)
        if isinstance(node, ast.Dict):
            result = {}
            known = True
            for key, value in zip(node.keys, node.values):
                k, v = self.expr(key), self.expr(value)
                if not isinstance(k, (str, int)):
                    known = False
                else:
                    result[k] = v
            return result if known else UNKNOWN
        if isinstance(node, ast.BinOp):
            left, right = self.expr(node.left), self.expr(node.right)
            if isinstance(node.op, ast.Add):
                return self.add(left, right)
            return UNKNOWN
        if isinstance(node, ast.JoinedStr):
            chunks = []
            known = True
            for part in node.values:
                if isinstance(part, ast.Constant):
                    chunks.append(part.value)
                else:
                    value = self.expr(part.value)
                    self.expr(part.format_spec)
                    if not isinstance(value, (str, int, float, bool)) or part.format_spec:
                        known = False
                    else:
                        chunks.append(repr(value) if part.conversion == 114 else ascii(value) if part.conversion == 97 else str(value))
            result = ''.join(chunks)
            return result if known and len(result) <= MAX_TEXT else UNKNOWN
        if isinstance(node, ast.Subscript):
            value = self.expr(node.value)
            index_node = node.slice.value if isinstance(node.slice, ast.Index) else node.slice
            index = self.expr(index_node)
            if isinstance(value, (tuple, dict, str)) and isinstance(index, (str, int)):
                try:
                    return value[index]
                except (KeyError, IndexError, TypeError):
                    pass
            if isinstance(value, Symbol) and value.name == 'builtins' and isinstance(index, str):
                return Symbol('builtins.' + index)
            return Symbol('?dynamic') if _may_load(value) else UNKNOWN
        if isinstance(node, ast.IfExp):
            self.expr(node.test)
            before = dict(self.env)
            left = self.expr(node.body)
            left_env = self.env
            self.env = dict(before)
            right = self.expr(node.orelse)
            right_env = self.env
            self.env = self.merge([left_env, right_env])
            if left == right:
                return left
            return Symbol('?dynamic') if _may_load(left) or _may_load(right) else UNKNOWN
        if isinstance(node, ast.BoolOp):
            outcomes = []
            values = []
            for child in node.values:
                values.append(self.expr(child))
                outcomes.append(dict(self.env))
            self.env = self.merge(outcomes)
            return Symbol('?dynamic') if any(_may_load(value) for value in values) else UNKNOWN
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            outer = self.env
            self.env = dict(outer)
            for generator in node.generators:
                self.expr(generator.iter)
                self.bind(generator.target)
                for condition in generator.ifs:
                    self.expr(condition)
            if isinstance(node, ast.DictComp):
                self.expr(node.key)
                self.expr(node.value)
            else:
                self.expr(node.elt)
            self.env = outer
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.NamedExpr):
                    self.bind(descendant.target)
            return UNKNOWN
        if isinstance(node, ast.NamedExpr):
            value = self.expr(node.value)
            self.bind(node.target, value)
            return value
        if isinstance(node, ast.Lambda):
            default_loaders = self.default_loaders(node.args)
            outer = self.env
            self.env = dict(outer)
            for name in _local_names(node):
                self.env[name] = UNKNOWN
            for name in default_loaders:
                self.env[name] = Symbol('?dynamic')
            self.expr(node.body)
            self.env = outer
            return UNKNOWN
        if isinstance(node, ast.Call):
            return self.call(node)
        for child in ast.iter_child_nodes(node):
            self.expr(child)
        return UNKNOWN

    def merge(self, outcomes):
        result = {}
        for name in set().union(*(set(outcome) for outcome in outcomes)):
            values = [outcome.get(name, BUILTINS.get(name, UNKNOWN)) for outcome in outcomes]
            if all(value == values[0] for value in values):
                result[name] = values[0]
            elif any(_may_load(value) for value in values):
                result[name] = Symbol('?dynamic')
            else:
                result[name] = UNKNOWN
        return result

    def default_loaders(self, args):
        parameters = args.posonlyargs + args.args
        pairs = list(zip(parameters[len(parameters) - len(args.defaults):], args.defaults))
        pairs += [(arg, value) for arg, value in zip(args.kwonlyargs, args.kw_defaults) if value is not None]
        return [arg.arg for arg, value in pairs if _may_load(self.expr(value))]

    def call(self, node):
        function = self.expr(node.func)
        args = [self.expr(arg) for arg in node.args]
        keywords = {kw.arg: self.expr(kw.value) for kw in node.keywords}
        name = function.name if isinstance(function, Symbol) else None
        if name in LOADERS:
            return self.load(node, name, args, keywords)
        if name and name.startswith('?dynamic'):
            self.error(node, 'Cannot resolve conditionally bound dynamic import callable')
            return UNKNOWN
        if name in ('builtins.exec', 'builtins.eval'):
            value = args[0] if args else keywords.get('source', UNKNOWN)
            outer = self.env
            supplied = args[1:3] if len(args) > 1 else [keywords[key] for key in ('globals', 'locals') if key in keywords]
            if supplied:
                self.env = dict(outer)
                for namespace in supplied:
                    if isinstance(namespace, dict):
                        self.env.update(namespace)
                    elif namespace is not None:
                        self.error(node, 'Cannot resolve dynamically executed code namespace')
            value = self.code(node, value, 'eval' if name == 'builtins.eval' else 'exec')
            if supplied:
                self.env = outer
            return value
        if name == 'builtins.compile':
            source = args[0] if args else keywords.get('source', UNKNOWN)
            mode = args[2] if len(args) > 2 else keywords.get('mode', UNKNOWN)
            return Code(source, mode) if isinstance(source, str) and mode in ('exec', 'eval', 'single') else UNKNOWN
        if name in ('builtins.globals', 'builtins.locals'):
            return dict(self.env)
        if name == 'builtins.getattr' and len(args) >= 2:
            if isinstance(args[0], Symbol) and isinstance(args[1], str):
                return Symbol(args[0].name + '.' + args[1])
            if isinstance(args[0], Symbol) and args[0].name in ('importlib', 'builtins'):
                return Symbol('?dynamic')
        # Support common constant module-name construction without invoking user code.
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'join' and len(args) == 1:
            separator = self.expr(node.func.value)
            items = args[0]
            if isinstance(separator, str) and isinstance(items, tuple) and all(isinstance(x, str) for x in items):
                if sum(map(len, items)) + len(separator) * len(items) <= MAX_TEXT:
                    return separator.join(items)
        if any(_may_load(arg) for arg in args + list(keywords.values())):
            self.error(node, 'Dynamic import callable escapes static analysis')
        # Calls mutating a tracked container make later target construction unknown.
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            receiver = node.func.value.id
            if isinstance(self.env.get(receiver), (tuple, dict)):
                self.env[receiver] = UNKNOWN
        return UNKNOWN

    def load(self, node, loader, args, keywords):
        parameters = ('name', 'package') if loader == 'importlib.import_module' else ('name', 'globals', 'locals', 'fromlist', 'level')
        if len(args) > len(parameters) or None in keywords or any(isinstance(arg, ast.Starred) for arg in node.args):
            self.error(node, 'Cannot resolve dynamic import arguments')
            return UNKNOWN
        options = dict(zip(parameters, args))
        if any(key not in parameters or key in options for key in keywords):
            self.error(node, 'Cannot resolve dynamic import arguments')
            return UNKNOWN
        options.update(keywords)
        module = options.get('name', UNKNOWN)
        if not isinstance(module, str) or len(module) > MAX_TEXT:
            self.error(node, 'Cannot resolve dynamic import module name')
            return UNKNOWN
        names = ()
        if loader == 'importlib.import_module':
            level = len(module) - len(module.lstrip('.'))
            package = options.get('package', UNKNOWN)
            if level:
                module = module[level:]
        else:
            level = options.get('level', 0)
            context = options.get('globals', {})
            package = context.get('__package__', UNKNOWN) if isinstance(context, dict) else UNKNOWN
            names = options.get('fromlist', ())
            if names is None:
                names = ()
            if not isinstance(names, (tuple, list)) or not all(isinstance(n, str) for n in names):
                self.error(node, 'Cannot resolve dynamic import fromlist')
                return UNKNOWN
        if not isinstance(level, int) or level < 0:
            self.error(node, 'Cannot resolve dynamic import level')
            return UNKNOWN
        if level:
            if not isinstance(package, str) or not package or level > len(package.split('.')):
                self.error(node, 'Cannot resolve relative dynamic import package')
                return UNKNOWN
            module = '.'.join(package.split('.')[:len(package.split('.')) - level + 1] + ([module] if module else []))
        if not module or any(not part or '/' in part or '\\' in part for part in module.split('.')):
            self.error(node, 'Cannot resolve dynamic import module name')
            return UNKNOWN
        reference = ast.ImportFrom(module=module, names=[ast.alias(name=n, asname=None) for n in names], level=0) if names else ast.Import(names=[ast.alias(name=module, asname=None)])
        ast.copy_location(reference, node)
        self.record(reference)
        return Symbol(module if names or loader == 'importlib.import_module' else module.split('.')[0])

    def code(self, node, value, mode):
        if isinstance(value, Code):
            value, mode = value.source, value.mode
        self.code_expansions += 1
        self.code_bytes += len(value) if isinstance(value, str) else 0
        if (not isinstance(value, str) or len(value) > MAX_TEXT or self.depth >= MAX_CODE_DEPTH
                or self.code_expansions > 64 or self.code_bytes > MAX_TEXT * 4):
            self.error(node, 'Cannot inspect dynamically executed code')
            return UNKNOWN
        try:
            tree = ast.parse(value, mode=mode)
        except (SyntaxError, ValueError, RecursionError):
            self.error(node, 'Cannot parse dynamically executed code')
            return UNKNOWN
        origin = self.origin
        self.origin = origin if origin is not None else node
        self.depth += 1
        value = self.expr(tree.body) if isinstance(tree, ast.Expression) else self.visit(tree)
        self.depth -= 1
        self.origin = origin
        return value if isinstance(tree, ast.Expression) else UNKNOWN


def _local_names(node):
    names = set()
    declarations = set()
    args = getattr(node, 'args', None)
    if args:
        names.update(arg.arg for arg in args.posonlyargs + args.args + args.kwonlyargs)
        if args.vararg:
            names.add(args.vararg.arg)
        if args.kwarg:
            names.add(args.kwarg.arg)

    def collect(current):
        for child in ast.iter_child_nodes(current):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(child.name)
            elif isinstance(child, (ast.Global, ast.Nonlocal)):
                declarations.update(child.names)
            elif isinstance(child, ast.Lambda):
                continue
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for descendant in ast.walk(child):
                    if isinstance(descendant, ast.NamedExpr) and isinstance(descendant.target, ast.Name):
                        names.add(descendant.target.id)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                names.add(child.id)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                names.update(alias.asname or alias.name.split('.')[0] for alias in child.names)
            else:
                collect(child)
    collect(node)
    return names - declarations


def _may_load(value):
    if isinstance(value, (tuple, list)):
        return any(_may_load(item) for item in value)
    if isinstance(value, dict):
        return any(_may_load(item) for item in value.values())
    return isinstance(value, Symbol) and (value.name in LOADERS or value.name in ('importlib', 'builtins') or value.name.startswith('?dynamic'))
