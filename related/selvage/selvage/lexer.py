"""Lexer with Pythonic significant indentation.

Blocks open by indentation and close by dedentation; there is no `end`.
Inside parentheses or brackets, line breaks are ignored.
"""
from .forms import Fault


class Tok:
    __slots__ = ('kind', 'val', 'line')

    def __init__(self, kind, val, line):
        self.kind, self.val, self.line = kind, val, line

    def __repr__(self):
        return f'{self.kind}:{self.val!r}@{self.line}'


OPS = ['<->', 'not=', '->', '<-', '<=', '>=', '=>', '=', '<', '>', '+', '-', '*', '/',
       '(', ')', '[', ']', ',', '.', ':']


class SyntaxFault(Fault):
    pass


def lex(src):
    toks = []
    indents = [0]
    depth = 0
    lines = src.split('\n')
    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        # strip comment (not inside a string)
        out, in_str = [], False
        for ch in line:
            if ch == '"':
                in_str = not in_str
            if ch == '#' and not in_str:
                break
            out.append(ch)
        line = ''.join(out).rstrip()
        if not line.strip():
            continue
        if '\t' in line[:len(line) - len(line.lstrip())]:
            raise SyntaxFault(f'line {ln}: tabs are not allowed in indentation')
        if depth == 0:
            ind = len(line) - len(line.lstrip(' '))
            if ind > indents[-1]:
                indents.append(ind)
                toks.append(Tok('INDENT', ind, ln))
            else:
                while ind < indents[-1]:
                    indents.pop()
                    toks.append(Tok('DEDENT', ind, ln))
                if ind != indents[-1]:
                    raise SyntaxFault(f'line {ln}: inconsistent indentation')
        i = len(line) - len(line.lstrip(' '))
        n = len(line)
        while i < n:
            c = line[i]
            if c == ' ':
                i += 1
                continue
            if c == '"':
                j = i + 1
                buf = []
                while j < n and line[j] != '"':
                    if line[j] == '\\' and j + 1 < n:
                        buf.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\'}.get(line[j + 1], line[j + 1]))
                        j += 2
                        continue
                    buf.append(line[j])
                    j += 1
                if j >= n:
                    raise SyntaxFault(f'line {ln}: unterminated text')
                if '\0' in buf:
                    # Text is for output; a NUL byte is invisible in source and would end the
                    # text early in compiled code, so it is refused rather than guessed at
                    raise SyntaxFault(f'line {ln}: text cannot hold a NUL byte')
                toks.append(Tok('STR', ''.join(buf), ln))
                i = j + 1
                continue
            if c.isdigit():
                j = i
                if line.startswith(('0x', '0X', '0b', '0B', '0o', '0O'), i):
                    j = i + 2
                    while j < n and (line[j].isalnum() or line[j] == '_'):
                        j += 1
                    is_float = False
                else:
                    while j < n and (line[j].isdigit() or line[j] == '_'):
                        j += 1
                    is_float = False
                    if j < n and line[j] == '.' and j + 1 < n and line[j + 1].isdigit():
                        is_float = True
                        j += 1
                        while j < n and (line[j].isdigit() or line[j] == '_'):
                            j += 1
                    if j < n and line[j] in 'eE':
                        k = j + 1
                        if k < n and line[k] in '+-':
                            k += 1
                        if k < n and line[k].isdigit():
                            is_float = True
                            j = k
                            while j < n and line[j].isdigit():
                                j += 1
                if j < n and (line[j].isalpha() or line[j] == '_'):
                    raise SyntaxFault(f'line {ln}: bad number {line[i:j + 1]!r}')
                text = line[i:j].replace('_', '')
                try:
                    if is_float:
                        toks.append(Tok('FLOAT', float(text), ln))
                    else:
                        toks.append(Tok('INT', int(text, 0), ln))
                except ValueError:
                    raise SyntaxFault(f'line {ln}: bad number {line[i:j]!r}')
                i = j
                continue
            if c.isalpha() or c == '_':
                j = i
                while j < n and (line[j].isalnum() or line[j] == '_'):
                    j += 1
                word = line[i:j]
                if word == 'not' and line[j:j + 1] == '=':
                    toks.append(Tok('OP', 'not=', ln))
                    i = j + 1
                    continue
                toks.append(Tok('NAME', word, ln))
                i = j
                continue
            for op in OPS:
                if line.startswith(op, i):
                    toks.append(Tok('OP', op, ln))
                    if op in '([':
                        depth += 1
                    elif op in ')]':
                        depth -= 1
                        if depth < 0:
                            raise SyntaxFault(f'line {ln}: unbalanced {op}')
                    i += len(op)
                    break
            else:
                raise SyntaxFault(f'line {ln}: unexpected character {c!r}')
        if depth == 0:
            toks.append(Tok('NEWLINE', None, ln))
    if depth:
        raise SyntaxFault('unbalanced brackets at end of file')
    last = len(lines)
    while len(indents) > 1:
        indents.pop()
        toks.append(Tok('DEDENT', 0, last))
    toks.append(Tok('EOF', None, last))
    return toks
