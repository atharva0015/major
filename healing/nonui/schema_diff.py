"""OpenAPI spec diff: structured breaking vs non-breaking changes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecChange:
    path: str
    kind: str  # removed_field|renamed_field|new_required|type_change|auth_change|added_optional
    detail: str
    breaking: bool


@dataclass(frozen=True)
class SchemaDiff:
    changes: tuple[SpecChange, ...] = ()

    @property
    def breaking(self) -> tuple[SpecChange, ...]:
        return tuple(c for c in self.changes if c.breaking)

    @property
    def has_breaking(self) -> bool:
        return bool(self.breaking)


def _fields(resp: object) -> dict[str, str]:
    if isinstance(resp, dict):
        fields = resp.get("fields", {})
        return dict(fields) if isinstance(fields, dict) else {}
    return {}


def diff_specs(base: dict[str, object], head: dict[str, object]) -> SchemaDiff:
    """Compare two minimal specs; classify each change. Pure function."""
    out: list[SpecChange] = []
    renamed_targets: set[tuple[str, str]] = set()
    base_paths = base.get("paths", {})
    head_paths = head.get("paths", {})
    assert isinstance(base_paths, dict) and isinstance(head_paths, dict)

    for path, ops in base_paths.items():
        if path not in head_paths:
            out.append(SpecChange(path, "removed_endpoint", f"{path} gone", True))
            continue
        assert isinstance(ops, dict)
        for op, spec in ops.items():
            hspec = head_paths[path].get(op, {}) if isinstance(head_paths[path], dict) else {}
            assert isinstance(spec, dict) and isinstance(hspec, dict)
            # responses live under method -> responses -> 200 -> fields
            bf = _fields((spec.get("responses") or {}).get("200", {}))
            hf = _fields((hspec.get("responses") or {}).get("200", {}))
            for name in bf:
                if name not in hf:
                    # Rename if a same-typed new field appeared, else removal.
                    same = [n for n, t in hf.items() if t == bf[name] and n not in bf]
                    if same:
                        out.append(SpecChange(path, "renamed_field", f"{name}->{same[0]}", True))
                        renamed_targets.add((path, same[0]))
                    else:
                        out.append(SpecChange(path, "removed_field", f"{name} removed", True))
            for name, typ in hf.items():
                if name not in bf:
                    if (path, name) in renamed_targets:
                        continue  # paired with a rename, not a separate addition
                    out.append(SpecChange(path, "added_optional", f"{name} added", False))
                elif bf[name] != typ:
                    out.append(SpecChange(path, "type_change", f"{name}: {bf[name]}->{typ}", True))
            breq = set(spec.get("required", []) or [])
            hreq = set(hspec.get("required", []) or [])
            for name in hreq - breq:
                out.append(SpecChange(path, "new_required", f"{name} now required", True))
    for path in head_paths:
        if path not in base_paths:
            out.append(SpecChange(path, "added_optional", f"{path} added", False))

    if base.get("auth") != head.get("auth"):
        out.append(
            SpecChange("(auth)", "auth_change", f"{base.get('auth')}->{head.get('auth')}", True)
        )
    return SchemaDiff(tuple(out))
