## 🔐 Golden Rules (NOT violate these)

1. Plugins must not import from tests/ at runtime
(TYPE_CHECKING hack is OK — you already do this correctly)
2. Fixtures own lifecycle & path (happy vs raw)
3. Helpers do NOT manage fixtures
4. Tests do NOT import helpers
5. Rollback must be trivial (git revert one file)