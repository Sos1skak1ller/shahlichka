# X5 Рост — от ростка к плоду, v2

Пять отдельных PNG 1024 × 1536. Стадии 2 и 5 — побитовые копии обязательных референсов лэндинга. Стадии 1, 3 и 4 созданы заново встроенным image_gen. Предыдущая прерванная генерация не входит в комплект.

1. **Почка** — Собранная спокойная поза, обе руки в кармане, ноги рядом. Файл: [stage-01-bud.png](stage-01-bud.png).
2. **Листик** — Одна рука в кармане, вторая приветственно поднята. Файл: [stage-02-leaf.png](stage-02-leaf.png).
3. **Завязь** — Шаг вперёд, открытая ладонь, свободная вторая рука. Файл: [stage-03-fruit-set.png](stage-03-fruit-set.png).
4. **Созревающий плод** — Устойчивая стойка, поднятый победный кулачок, вторая рука у кармана. Файл: [stage-04-ripening.png](stage-04-ripening.png).
5. **Апельсинка** — Обе руки вверх, одна нога поднята: празднование награды. Файл: [stage-05-orange.png](stage-05-orange.png).

Прогресс связан с подтверждёнными покупками. Числовые пороги и правила начисления в этой серии не задаются.

Матовая пластилиновая фактура, зелёная одежда, кремовые кеды и узнаваемый дизайн лица сохранены по референсам. Новые изображения не являются пиксельно идентичными оригиналам; у исходной Апельсинки уже есть кремовые обводки глаз, которые появляются и на четвёртой стадии. Поза четвёртой стадии: свободная рука у кармана, а не на поясе. У первой стадии верхушка состоит из двух сложенных половин листа.

Фон непрозрачный, как в оригиналах. Стадии 1–4 на кремовом фоне; финал сохраняет оригинальный зелёный фон и праздничные звёздочки. Фоновые линии служат только декором исходной стилистики, не механикой роста.

Ассеты сохранены отдельно; код лэндинга и существующие изображения не изменены.

## Промпты

Встроенный image_gen; для всех новых стадий использованы оба оригинальных референса:

- /Users/avtorygin/Documents/ChatGPT/aith-x5/shahlichka/web/public/assets/growth/hero/progress-leaf-clay-v2.png
- /Users/avtorygin/Documents/ChatGPT/aith-x5/shahlichka/web/public/assets/growth/hero/level-up-orange-clay-v2.png

### Стадия 1: bud

```text
Use case: stylized-concept.
Asset type: single production mascot portrait in a five-stage customer purchase progress series.
Input images: Reference 1 is the exact Leaf mascot from the approved landing page, the primary identity/material/outfit/lighting reference. Reference 2 is its approved Orange final form, secondary form reference. These are strict art-direction references. Reproduce the original clay studio's visual language with extreme fidelity.
Character invariants: identical facial feature shapes and placement as the Leaf reference, dark green oval eyes with small cream reflections, thick softly curved dark green eyebrows, tiny round nose, open happy smile with tiny orange tongue. Same deep forest green clay hoodie with lime drawstrings and knots, kangaroo pocket, thick cuffs and hood, same matching green trousers, identical chunky cream sneakers with green stripes and laces. Same body size, limb thickness, short neck and oversized head proportions. All surfaces hand-sculpted matte plasticine with the original fine irregular impressions, hoodie wrinkling and seams. Not knitted fabric, not fuzzy, not smooth vinyl. Soft warm diffuse light and contact shadow exactly like the references.
Framing: one full-body character, portrait 2:3, 1024x1536. Use Reference 1's scene placement: shoes near 94% canvas height, shoulders near 62%, head bottom near 61%, face in lower half of the head. Body and shoes stay the same scale between stages; changing head anatomy alone expresses growth. Entire figure and hands visible. Camera nearly frontal as original.
Backdrop: preserve Reference 1's warm cream textured backdrop and its faint static decorative green and lilac lines; these background marks are not progress or aura and should remain understated. No extra symbols.
No text, digits, logos, UI, additional characters, props, accessories, costume changes, glow, neon, particles, rings around body, crowns, seedlings held in hands, or stickers. Output exactly one portrait, no collage.
Stage-specific form and pose:
Level 1, young closed LEAF BUD, before Reference 1's opened leaf. Head is a compact narrow upright green teardrop with two leaf halves softly folded together along a visible central crease; do not make it an onion or round fruit. Head maximum width around 34% canvas versus Reference 1's 43%; top around 35% canvas, chin at 61%. One pointed curved tip, lime green throughout, delicate leaf veins, no separate leaves or stem. Face remains same size as Reference 1. Pose: feet close, both hands tucked naturally in kangaroo pocket, shoulders relaxed, head gently tilted, warm calm smile. Full-size same clothed body, not a baby.
```

### Стадия 3: fruit-set

```text
Use case: stylized-concept.
Asset type: single production mascot portrait in a five-stage customer purchase progress series.
Input images: Reference 1 is the exact Leaf mascot from the approved landing page, the primary identity/material/outfit/lighting reference. Reference 2 is its approved Orange final form, secondary form reference. These are strict art-direction references. Reproduce the original clay studio's visual language with extreme fidelity.
Character invariants: identical facial feature shapes and placement as the Leaf reference, dark green oval eyes with small cream reflections, thick softly curved dark green eyebrows, tiny round nose, open happy smile with tiny orange tongue. Same deep forest green clay hoodie with lime drawstrings and knots, kangaroo pocket, thick cuffs and hood, same matching green trousers, identical chunky cream sneakers with green stripes and laces. Same body size, limb thickness, short neck and oversized head proportions. All surfaces hand-sculpted matte plasticine with the original fine irregular impressions, hoodie wrinkling and seams. Not knitted fabric, not fuzzy, not smooth vinyl. Soft warm diffuse light and contact shadow exactly like the references.
Framing: one full-body character, portrait 2:3, 1024x1536. Use Reference 1's scene placement: shoes near 94% canvas height, shoulders near 62%, head bottom near 61%, face in lower half of the head. Body and shoes stay the same scale between stages; changing head anatomy alone expresses growth. Entire figure and hands visible. Camera nearly frontal as original.
Backdrop: preserve Reference 1's warm cream textured backdrop and its faint static decorative green and lilac lines; these background marks are not progress or aura and should remain understated. No extra symbols.
No text, digits, logos, UI, additional characters, props, accessories, costume changes, glow, neon, particles, rings around body, crowns, seedlings held in hands, or stickers. Output exactly one portrait, no collage.
Stage-specific form and pose:
Level 3, LEAF BECOMING YOUNG FRUIT, the midpoint between both references. ONE unified green head, not two heads stacked. The lower two-thirds of the head expand into rounded lime-green fruit cheeks; the upper third tapers into the original single pointed leaf tip folded slightly backward. Read as a plump leaf with a rounded developing fruit base, visibly rounder than Reference 1 but not yet spherical. Central vein and leaf veins persist near top, becoming subtle near round lower cheeks. No orange skin yet, no stem or separate leaf yet. Head width around 45% canvas, top at 30%, chin at 61%. Same Leaf face integrated into round lower part. Pose: take one small step toward viewer, one cream shoe slightly forward grounded naturally, torso leaning gently forward. One arm extending a little outward with friendly open palm, the other relaxed beside hoodie. Keep lively movement subtle. Anatomically correct two arms and legs.
```

### Стадия 4: ripening

```text
Use case: stylized-concept.
Asset type: single production mascot portrait in a five-stage customer purchase progress series.
Input images: Reference 1 is the exact Leaf mascot from the approved landing page, the primary identity/material/outfit/lighting reference. Reference 2 is its approved Orange final form, secondary form reference. These are strict art-direction references. Reproduce the original clay studio's visual language with extreme fidelity.
Character invariants: identical facial feature shapes and placement as the Leaf reference, dark green oval eyes with small cream reflections, thick softly curved dark green eyebrows, tiny round nose, open happy smile with tiny orange tongue. Same deep forest green clay hoodie with lime drawstrings and knots, kangaroo pocket, thick cuffs and hood, same matching green trousers, identical chunky cream sneakers with green stripes and laces. Same body size, limb thickness, short neck and oversized head proportions. All surfaces hand-sculpted matte plasticine with the original fine irregular impressions, hoodie wrinkling and seams. Not knitted fabric, not fuzzy, not smooth vinyl. Soft warm diffuse light and contact shadow exactly like the references.
Framing: one full-body character, portrait 2:3, 1024x1536. Use Reference 1's scene placement: shoes near 94% canvas height, shoulders near 62%, head bottom near 61%, face in lower half of the head. Body and shoes stay the same scale between stages; changing head anatomy alone expresses growth. Entire figure and hands visible. Camera nearly frontal as original.
Backdrop: preserve Reference 1's warm cream textured backdrop and its faint static decorative green and lilac lines; these background marks are not progress or aura and should remain understated. No extra symbols.
No text, digits, logos, UI, additional characters, props, accessories, costume changes, glow, neon, particles, rings around body, crowns, seedlings held in hands, or stickers. Output exactly one portrait, no collage.
Stage-specific form and pose:
Level 4, RIPENING GREEN ORANGE, nearly the final form from Reference 2. Head is now a single spherical unripe citrus fruit, with the exact short green stalk and one large green leaf growing at top as in Reference 2. Match Reference 2's fine clay orange-peel impressions, softened in green. Fruit skin remains predominantly lime green: around 75% green, with one broad warm orange ripening blush on the viewer-right lower cheek and flank covering around 25% of head. The orange area is continuous matte skin pigment, soft organic boundary, not glow, painted circle, separate object or sticker. Keep same Leaf face and clothes. Head width around 46% canvas, spherical head top around 35% plus leaf to 28%, chin at 61%. Hands green. Pose: confidently planted feet slightly apart, one hand on hip, other arm bent with one small celebratory fist raised at shoulder height; torso open, warm smile. No jumping yet, no stars. Keep familiar gentle character rather than superhero. Exactly two arms/hands.
```

### Уточнение третьей стадии

Первый результат третьей стадии использован как редактируемая основа; оба оригинала снова переданы как референсы.

```text
Use case: precise-object-edit.
Image 1 is the EDIT TARGET, the generated third-stage mascot portrait. Image 2 is the original landing Leaf identity/style reference. Image 3 is the original landing Orange final-form reference.
Make one targeted change to Image 1: reshape ONLY the head silhouette and its surface anatomy into a clear midway stage between the leaf and spherical fruit. Preserve the existing face, exact eye/nose/mouth sizes, smile, body, pose, clothes, shoes, hands, lighting, backdrop and framing of Image 1.
The head should now be an almost round lime-green young fruit, with a SINGLE SHORT integrated leaf point curving back at its very top. Reduce the existing tall leaf tip to about ONE THIRD of its present height, while keeping the round head base, chin position and maximum width. The resulting total head is nearly as wide as tall, with a tiny tapered leaf crest continuous with its crown. It must read as a plump developing fruit, not an oversized leaf or pear. The bottom two-thirds have convex spherical cheeks and subtle handmade citrus impressions; leaf veins survive only in upper crown and short leaf tip. Blend the transition naturally in the same matte plasticine sculpting. All green, no orange yet. No stem, separate top leaf, props, added objects, changed costume, text or effects. Keep full body and complete original 2:3 canvas. Exact original handcrafted clay material quality.
```

