# Fable II TU1 indirect-function candidate discovery

`tools\Find-IndirectFunctionCandidates.py` is a deterministic, read-only
review aid for guest function targets reached only through indirect calls. It
does not modify `fable2_manifest.toml` and deliberately does not treat every
aligned executable address as a function.

Example using the TU1-patched bytes captured during Harvest 002:

```powershell
python .\tools\Find-IndirectFunctionCandidates.py `
    --dump .\out\fault-walk-runs\iteration-07\tu1-text-0x82000000.bin `
    --manifest .\fable2_manifest.toml `
    --generated-init .\generated\default\fable2_init.cpp `
    --target 0x829675C0 `
    --target 0x829675D0 `
    --target 0x8288ACB0 `
    --target 0x8288ACC0 `
    --target 0x82964820
```

The report combines three evidence types:

- exact big-endian pointers in non-executable PE sections and their containing
  contiguous pointer tables;
- conservative `lis` plus `addi`/`ori` address materialization in executable
  code;
- a strict four-instruction virtual-dispatch-thunk code shape, plus current
  manifest/generated registration status.

The global materialized-pointer review requires the computed address to be in
an executable PE section, the destination to be an ABI argument register
`r3-r10`, and a direct `bl` within four instructions. This is deliberately a
candidate rule, not a proof of a function boundary. Table membership can also
mix callbacks with ordinary data. Every missing address must therefore be
validated against TU1 bytes and control flow before a manifest override is
added.

## Confirmed discovery gaps

ReXGlue's current discovery phase invokes the RTTI-aware `VTableScanner`, which
requires an MSVC complete-object-locator/type-descriptor shape. Fable II also
uses non-RTTI callback arrays; these do not satisfy that scanner. ReXGlue has a
code-materialized function-pointer scan, but it is currently disabled because
its generic form produces false positives.

The harvested targets demonstrate both gaps:

- `0x8288ACB0`, `0x8288ACC0`, and the previously fixed `0x82C03B28` occur in
  non-RTTI `.rdata` callback/function-pointer structures.
- `0x829675C0`, `0x829675D0`, the previously fixed `0x829675E0`, and
  `0x82964820` are materialized in code and passed as callback arguments before
  later `mtctr`/`bctrl` dispatch.

Automatic bulk manifest insertion is not yet safe. The useful workflow is
candidate generation, TU1 boundary validation, review, then an explicit
manifest entry.

## Harvest 002 correctness entries

All ranges below are exclusive-end ranges proven from the TU1-patched image.
Each is now an explicit manifest entry and has a generated `DEFINE_REX_FUNC`
body plus dispatcher registration.

- `0x829675C0-0x829675D0`: four-instruction virtual-dispatch thunk using `r3`
  and vtable slot `0x44`. Its address is materialized at
  `0x82964B20/0x82964B28` and passed in `r6` to the direct call at
  `0x82964B34 -> 0x82965500`. Harvest 002 reached it through
  `0x822D2A98 mtctr r10; 0x822D2A9C bctrl`.
- `0x829675D0-0x829675E0`: four-instruction virtual-dispatch thunk using `r3`
  and slot `0x94`. Proven materializations include
  `0x826ECA14/0x826ECA1C` and `0x82964E18/0x82964E20`; the same Harvest 002
  indirect call site was `0x822D2A9C`.
- `0x8288ACB0-0x8288ACC0`: four-instruction virtual-dispatch thunk using `r3`
  and slot `0x14`. It is entry `20` at `.rdata` address `0x82009548` in the
  proven pointer table `[0x820094F8,0x8200954C)`. Harvest 002's caller was
  `0x8288BBAC mtctr r30; 0x8288BBB0 bctrl`.
- `0x8288ACC0-0x8288ACD0`: four-instruction virtual-dispatch thunk using `r3`
  and slot `0x08`. It is entry `17` at `.rdata` address `0x8200953C` in the
  same table. Harvest 002's caller was
  `0x8288B314 mtctr r4; 0x8288B318 bctrl`.
- `0x82964820-0x82964830`: four-instruction virtual-dispatch thunk using `r3`
  and slot `0x64`. Its address is materialized at
  `0x82961170/0x82961178`, passed in `r6`, and consumed by
  `0x82961184 -> 0x82962858`. Harvest 002 reached it through
  `0x8227DD38 mtctr r10; 0x8227DD3C bctrl`.

The exact manifest lines are:

```toml
"0x829675C0" = { size = 0x10 }
"0x829675D0" = { size = 0x10 }
"0x8288ACB0" = { size = 0x10 }
"0x8288ACC0" = { size = 0x10 }
"0x82964820" = { size = 0x10 }
```

The first pointer table also exposes `0x82C00A98-0x82C00AA8`, another exact
four-instruction thunk (slot `0x04`) absent from the manifest. It remains a
review candidate rather than an automatic insertion because it has not yet
been observed at runtime. Likewise the conservative materialization report
finds several exact sibling thunks near `0x82964800` and `0x82967530`, plus a
separate run near `0x8305DA68`; those are candidates, not current fixes.

## Harvest 002 findings intentionally left pending

- `0x82967540-0x82967550` is statically strong: an exact four-instruction `r3`
  virtual-dispatch thunk using slot `0x98`, materialized at
  `0x826ECA60/0x826ECA68` and `0x82964DCC/0x82964DD4`. It was not added because
  its Harvest 002 observation came after multiple synthetic returns; recurrence
  on the cleaner Harvest 003 path is the requested discriminator.
- `0x82C8A920-0x82C8A93C` occurs at `.rdata` address `0x8200E920`, slot `26` of
  the proven callback table `[0x8200E8B8,0x8200E940)`. Its neighboring function
  pointers are registered. This increases its static confidence, but it also
  remains pending cleaner runtime recurrence.
- `0x82DE2BA8-0x82DE2BC4` is a real adapter thunk: it moves `r4` to `r11`, moves
  `r5` to `r4`, loads `r3` through the saved pointer, and tail-dispatches vtable
  slot `0x24`. Neither byte order of its absolute address occurs in the loaded
  TU1 image, and the conservative `lis` plus `addi`/`ori` scan finds no match.
  Runtime instead reaches it through `0x82E060F8`: the paths at
  `0x82E06168-0x82E06194` index a runtime table from object state, load a
  function pointer with `lwzx`, then `mtctr`/`bctr`. This is a third pattern—a
  runtime-populated dispatch table whose ultimate initialization still needs
  tracing—rather than either of the two statically recoverable patterns above.
  Harvest 003 reproduced it as the third target after only two prior synthetic
  returns, substantially upgrading its runtime confidence.
