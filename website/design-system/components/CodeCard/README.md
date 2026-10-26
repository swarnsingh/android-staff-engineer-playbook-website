# CodeCard

A dark code block with a filename header and a copy button; the one dark object on the sheet in every theme.

## Rules

- `code-bg` in every theme, so Kotlin highlighting stays the same whether the reader picks light, dark or sepia.
- `codeBlock` (JetBrains Mono, 15/26) with `font-variant-ligatures: none`, so `->`, `!=` and `==` look exactly as typed.
- Long lines scroll inside the card; the page never scrolls sideways. A reader setting can switch the card to wrapping.
- The Copy button writes the code to the clipboard and says "Copied". Where the clipboard is refused, it selects the code and asks for Ctrl/Cmd+C.
- The header names the file and, in one short line, what the example assumes.
- Syntax colours: `code-key` for keywords and annotations, `code-call` for function and type names, `code-string` for literals, `code-comment` for comments. Every colour is at least 4.5:1 on `code-bg`.

## Tokens

`code-bg`, `code-ink`, `code-key`, `code-call`, `code-string`, `code-comment`, `line-strong`, `radius-md`, `radius-pill`.
