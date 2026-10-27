# Callout

A tinted block inside the sheet that sets one passage apart. Four kinds, told apart by tint and a capital label, not by icons or a side bar.

| Kind | Tint | Label | Use |
|---|---|---|---|
| Start here | `accent-soft` | `accent` | The problem-first opening story. Once per lesson. |
| Staff note | `sheet-sunken` | `ink` | The staff-engineer judgement for a section. |
| Remember | `event-soft` | `event` | One fact the reader must carry forward. At most two per lesson. |
| Under review | `warn-soft` | `warn` | Names a passage of the original chapter that is under technical review. Never states the replacement. |

## Rules

- No border, no shadow, no left accent bar. The tint and the label carry the meaning. High contrast swaps the tint for a 1px `line` border.
- Text uses `bodyLarge` at 17px, so a callout reads as part of the lesson. Under review notes use 15px because they are about the text, not part of it.
- Label text on its fill meets 4.5:1 in every theme.
- Handwriting is not used in callouts. The demo's handwritten "Remember!" is replaced by the label.

## Tokens

`accent-soft`, `accent`, `on-accent`, `sheet-sunken`, `ink`, `event-soft`, `event`, `warn-soft`, `warn`, `sheet`, `radius-md`, `radius-pill`.
