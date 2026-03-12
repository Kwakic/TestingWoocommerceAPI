import json
from typing import Any


def truncate_preview(obj: Any, max_chars: int = 1000) -> str:
    """
    🔍 Safely serialize and truncate large exception messages or payloads.

    Return a JSON-ish string preview of obj truncated to max_chars.
    Works for exceptions, dicts, lists, and other objects (falls back to repr()).

    - Uses JSON formatting for readability (e.g., API responses).
    - Falls back to repr() only if JSON serialization fails.
    - Prevents overly long messages in pytest logs.

    Why:
        - repr(e)[:300] can cut off text mid-sentence and show escaped \n
        - This keeps JSON & text readable while still preventing log flooding.

    Behavior:
    - If `obj` is a str or bytes, return it (bytes decoded with errors='replace').
    - Otherwise try json.dumps(obj, default=str) to produce a compact representation.
    - On TypeError/ValueError/OverflowError fall back to repr(obj).

    Args:
        obj: The object or exception to represent as text.
        max_chars: Maximum allowed characters before truncation.


    Returns:
        A human-readable string, truncated if longer than `max_chars`.
    """
    try:
        # Exceptions may not be JSON serializable; str(obj) is safer.
        if isinstance(obj, (str, bytes)):
            text = obj.decode(errors="replace") if isinstance(obj, bytes) else obj
        else:
            # Try to produce compact JSON for common objects
            text = json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":"), indent=None)
    except (TypeError, ValueError, OverflowError):
        #  Non-serializable objects fallback to repr()
        text = repr(obj)

    if len(text) > max_chars:
        return text[:max_chars] + "...(truncated)"
    return text


"""
⚙️ 1️⃣ Example with repr(e)[:300]

Let’s say your WooCommerce /products endpoint returns a broken JSON schema, and your exception looks like:

ValidationError: 'price' is not of type 'number'
"
Failed validating 'type' in schema['properties']['price']:
    {'type': 'number'}
On instance['price']:
    '24.99'
"

But when printed via repr(e)[:300], your pytest log line might look like this:
"
products: schema validation failed for id=102 (sample_size=10, fail_on_empty=True): ValidationError("'price' is not of 
type 'number'\n\nFailed validating 'type' in schema['properties']['price']:\n    {'type': 'number'}\nOn instance
['price']:\n    '24.99'")...
"
Notice:
- It’s Python-escaped (\n instead of newlines).
- It’s cut off mid-sentence because of the [:300] truncation.
- It’s hard to read in CI logs.

⚙️ 2️⃣ Example with _truncate_preview(e)
Now, if you used:
"
pytest.fail(f"{endpoint}: validation request failed: {_truncate_preview(e)}")
"
and _truncate_preview() was defined as:
"
def _truncate_preview(obj: Any, max_chars: int = 1000) -> str:
    try:
        text = json.dumps(obj, default=str, ensure_ascii=False, indent=None)
    except Exception:
        text = repr(obj)
    if len(text) > max_chars:
        return text[:max_chars] + "...(truncated)"
    return text
"
Your log would look like this:
"
products: schema validation failed for id=102 (sample_size=10, fail_on_empty=True): 
"ValidationError: 'price' is not of type 'number'

Failed validating 'type' in schema['properties']['price']:
    {'type': 'number'}
On instance['price']:
    '24.99'"
"
Notice:
✅ Readable newlines (not \n)
✅ Proper quoting and Unicode-safe output
✅ Still truncated if too long, but gracefully with ...(truncated)

⚙️ 3️⃣ Bigger example — API 500 error
Imagine the API returns a long JSON error:
"
{
  "code": "woocommerce_rest_cannot_view",
  "message": "Sorry, you cannot list resources.",
  "data": {"status": 401, "params": {...large object...}}
}
"
Using repr(e)[:300]:
"
orders: failed to fetch list (fail_on_empty=False): Exception("APIError: {'code': 'woocommerce_rest_cannot_view', 
'message': 'Sorry, you cannot list resources.', 'data': {'status': 401, 'params': {...}}}")[:300]
"
Hard to read.
All inline, with truncated braces, no clear JSON formatting.

Using _truncate_preview(e):
"
orders: failed to fetch list (fail_on_empty=False): 
{
  "code": "woocommerce_rest_cannot_view",
  "message": "Sorry, you cannot list resources.",
  "data": {"status": 401, "params": {...}}
}...(truncated)
"
Readable, structured, CI-friendly.
No escaping or half-cut text.

"""
