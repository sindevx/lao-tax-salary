# แผนแก้ UX/UI & Accessibility — Lao Tax Salary Calculator

**Branch:** `feat/ux-a11y-improvements`  
**เป้าหมาย:** ปรับ UX/UI และ accessibility ตาม `ux-ui-review.html`  
**ข้อจำกัด:** **ห้ามแก้ business logic** — ไม่แตะ `calculateSalary`, `calculatePIT`, tax brackets, validation rules, localStorage schema, i18n keys/values

**ขอบเขตที่แก้ได้:** HTML structure, CSS, ARIA attributes, semantic markup, icons (emoji → SVG), `lang` attribute, focus/skip links, motion CSS

---

## หลักการทำงาน

| ทำ | ไม่ทำ |
|----|--------|
| เพิ่ม `for`/`id`, `aria-*`, landmarks | เปลี่ยนสูตรภาษี / bracket |
| แทน emoji ด้วย SVG (visual เท่านั้น) | Refactor ฟังก์ชันคำนวณ |
| CSS: typography, reduced-motion, scrim | เปลี่ยน flow การ validate |
| Implement `printReport()` เป็น UI wrapper (`window.print`) | แก้ `validateInputs()` logic |
| ซ่อนปุ่มที่พังชั่วคราว (ถ้ายังไม่ implement) | แยกไฟล์ JS ทั้งก้อน (out of scope) |

**การ verify แต่ละ step:** เปิด `index.html` → คำนวณเดิมได้ผลเท่าเดิม → Tab/screen reader ดีขึ้น → ไม่มี regression บน mobile 375px

---

## Phase 0 — เตรียมงาน (ทำแล้ว)

- [x] รีวิว UX/UI → `ux-ui-review.html`
- [x] สร้าง branch `feat/ux-a11y-improvements`
- [x] เขียนแผนนี้

## Implementation status (24 May 2026)

- [x] Phase 1 — Accessibility foundation
- [x] Phase 2 — Emoji → SVG
- [x] Phase 3 — `printReport()` + print CSS
- [x] Phase 4 — Typography mobile + reduced-motion + scrim
- [x] Phase 5 — focus-visible, Esc dismiss, results focus
- [ ] Phase 6 — Out of scope (dark mode, Tailwind build)

**Commit แนะนำ (optional):** เพิ่ม `ux-ui-review.html` + `docs/UX-IMPLEMENTATION-PLAN.md` เป็น docs only

---

## Phase 1 — Accessibility foundation (Critical, ไม่แตะ JS logic)

**เป้าหมาย:** WCAG พื้นฐาน — form labels, landmarks, live regions

| # | งาน | ไฟล์ | แตะ logic? |
|---|-----|------|------------|
| 1.1 | เพิ่ม `id` ให้ input/select ที่มี label แล้วผูก `for="..."` | `index.html` | ไม่ |
| 1.2 | `<main id="main-content">` + skip link `<a href="#main-content" class="sr-only focus:not-sr-only">` | HTML + CSS | ไม่ |
| 1.3 | `nav` bottom bar: `aria-label="Main navigation"` | HTML | ไม่ |
| 1.4 | ปุ่มปิด panel: `aria-label` (i18n ผ่าน `data-i18n` หรือ attribute คงที่ EN/LO ใน HTML) | HTML | ไม่ |
| 1.5 | SSO Yes/No: `role="group"` + `aria-label` + `aria-pressed="true/false"` — **อัปเดต attribute ใน `setSocialSecurity()` เท่านั้น** (ไม่เปลี่ยนเงื่อนไขคำนวณ) | HTML + JS 2 บรรทัด attribute | ไม่แตะ calc |
| 1.6 | `#results`: `aria-live="polite"` + `aria-atomic="true"` เมื่อแสดงผล — toggle class/attribute ใน `calculateSalary()` หลังแสดง results (ไม่แตะตัวเลข) | HTML + JS display only | ไม่แตะ calc |
| 1.7 | `toggleLanguage()`: ตั้ง `document.documentElement.lang` เป็น `en` / `lo` | JS 1–2 บรรทัด | ไม่แตะ calc |

**Definition of done Phase 1:** Lighthouse/axe — form labels pass; กด Tab ข้าม skip link ได้; SSO ประกาศสถานะ pressed

**Commit:** `feat(a11y): form labels, landmarks, and live regions`

---

## Phase 2 — แทนที่ Emoji ด้วย SVG (Visual only)

**เป้าหมาย:** ไม่ใช้ emoji เป็น structural UI (UI Pro Max)

| # | ตำแหน่ง | แทนที่ด้วย |
|---|----------|------------|
| 2.1 | Header logo 🇱🇦 | SVG flag หรือ icon calculator + `aria-hidden` |
| 2.2 | Language toggle 🇬🇧 | SVG globe หรือข้อความ "EN"/"ລາວ" เท่านั้น |
| 2.3 | Currency options 🇺🇸/🇱🇦 | ข้อความ "USD" / "LAK" ใน `<option>` (ลบ emoji) |
| 2.4 | Overtime ⏰, Other 📋, Breakdown 📊 | SVG Heroicons (clock, clipboard, chart) — `aria-hidden` + ข้อความ label เดิม |

**Definition of done Phase 2:** ไม่มี emoji ใน DOM ที่เป็น icon; หน้าตาและ i18n ข้อความเหมือนเดิม

**Commit:** `feat(ui): replace emoji icons with inline SVG`

---

## Phase 3 — Broken UX: Print (wrapper only)

**เป้าหมาย:** ปุ่ม Print ไม่ throw `ReferenceError`

| # | งาน | รายละเอียด |
|---|-----|------------|
| 3.1 | เพิ่ม `function printReport() { window.print(); }` | ไม่คำนวณใหม่ — แค่เรียก print dialog |
| 3.2 | (Optional) `@media print` ซ่อน bottom nav / แสดงเฉพาะ results | CSS only |

**Definition of done Phase 3:** กด Print ไม่ error; พิมพ์ได้เมื่อมี results

**Commit:** `fix(ui): implement printReport via window.print`

---

## Phase 4 — Typography & motion (CSS only)

| # | งาน |
|---|-----|
| 4.1 | ลบ/ผ่อน media rule ที่บังคับ `h1 { font-size: 1rem }` — ใช้ `text-base`/`text-lg` ขั้นต่ำ |
| 4.2 | ใน `#results` / breakdown: ยก `text-xs` เป็น `text-sm` ที่อ่านยาก (ไม่แตะตัวเลข) |
| 4.3 | `@media (prefers-reduced-motion: reduce)` ปิด `animate-*`, `pulse-soft`, sheet transition |
| 4.4 | Bottom sheet overlay: `rgba(0,0,0,0.45)` แทน `0.3` |

**Definition of done Phase 4:** อ่านง่ายขึ้นบน 375px; reduced-motion ปิด animation

**Commit:** `style(ui): improve mobile type and respect reduced-motion`

---

## Phase 5 — Focus & keyboard polish (Low risk)

| # | งาน |
|---|-----|
| 5.1 | `.toggle-option:focus-visible`, nav buttons `:focus-visible` ring |
| 5.2 | ปุ่ม X: `min-width/height 44px` (padding) — hit area |
| 5.3 | Modal/sheet: ปิดด้วย `Escape` — listener เพิ่ม/ปิด modal เท่านั้น (ไม่แตะ calc) |
| 5.4 | หลัง `calculateSalary()` สำเร็จ: `results.focus()` หรือ `scrollIntoView` (UX only) |

**Commit:** `feat(a11y): focus-visible and keyboard dismiss for modals`

---

## Phase 6 — Out of scope (ทำภายหลัง / แยก PR)

| รายการ | เหตุผลเลื่อน |
|--------|----------------|
| Dark mode | ต้องออกแบบ token ทั้งแอป — แยก PR |
| Tailwind CDN → build | DevOps / build pipeline — ไม่ใช่ UX-only |
| แยก `index.html` เป็น modules | Maintainability ใหญ่ — เสี่ยงแตะ logic |
| Unit tests tax logic | แยกจาก UX branch |

---

## ลำดับ Commit ที่แนะนำ

```
1. docs: add UX review and implementation plan
2. feat(a11y): form labels, landmarks, and live regions
3. feat(ui): replace emoji icons with inline SVG
4. fix(ui): implement printReport via window.print
5. style(ui): improve mobile type and respect reduced-motion
6. feat(a11y): focus-visible and keyboard dismiss for modals
```

แต่ละ commit = 1 phase, review ได้ทีละชิ้น, revert ง่าย

---

## Checklist ก่อน merge กลับ `main`

- [ ] คำนวณเงินเดือนเดิม (USD/LAK, SSO on/off) ได้ผลเหมือนก่อนแก้
- [ ] Save / Load / Export XLSX ยังทำงาน
- [ ] EN ↔ LO สลับได้, `lang` ถูกต้อง
- [ ] Tab ครบทุก control, ไม่มี ReferenceError จาก Print
- [ ] ทด 375px portrait + safe area bottom nav
- [ ] เปิด `ux-ui-review.html` checklist — Critical ใน Phase 1–3 ปิดแล้ว

---

## เริ่ม implement ขั้นแรก

เมื่อ approve แผนนี้ → เริ่ม **Phase 1.1** เท่านั้น (label `for`/`id`) แล้ว commit แยกตามตารางด้านบน
