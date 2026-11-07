# D-013 Encoding, newlines and escaping

UTF-8 without BOM; strict decoding. Records end with LF only; CR anywhere is an error, and the file must end with LF. Control characters (U+0000–U+001F, U+007F–U+009F) are forbidden inside values. Delimiter `|`; inside a value `\|` means `|` and `\\` means `\`; any other backslash sequence is `MALFORMED_RECORD`.

**Why UTF-8 rather than ASCII:** `fulfillment.requested.v1` allows any string for `sku` (1–80 characters). An ASCII-only protocol would make some valid events unmappable. Lengths count Unicode code points, matching JSON Schema `maxLength`. The TUI shows non-ASCII characters as `\uXXXX` escapes, so the console stays ASCII-safe.
