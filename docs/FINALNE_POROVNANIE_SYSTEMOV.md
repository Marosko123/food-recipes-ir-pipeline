# Finálne Porovnanie Vyhľadávacích Systémov

**Autor:** Maroš Bednár  
**Dátum:** 09. December 2025  
**Predmet:** VINF - Vyhľadávanie Informácií

---

## 📋 Obsah

1. [Metodológia a metriky](#-metodológia-a-metriky)
2. [Analýza jednotlivých queries](#-analýza-jednotlivých-queries)
3. [Súhrnná štatistika](#-súhrnná-štatistika)
4. [Závery](#-závery)

---

## 🔬 Metodológia a metriky

### Testované systémy

| ID | Systém | Typ indexu | Metrika |
|----|--------|-----------|---------|
| **S1** | Simple BM25 | TSV invertovaný index | BM25 (Okapi) |
| **S2** | Simple TF-IDF | TSV invertovaný index | TF-IDF klasická |
| **L1** | Lucene BM25 | PyLucene binárny | BM25Similarity |
| **L2** | Lucene TF-IDF | PyLucene binárny | ClassicSimilarity |
| **FC** | Food.com | Produkčný (tag-based) | Proprietárny |

### 📐 Definície metrík

#### Precision@K (P@K)
$$\text{Precision@K} = \frac{\text{počet relevantných dokumentov v top K}}{K}$$

**Príklad:** Ak z 5 vrátených dokumentov sú 3 relevantné → P@5 = 3/5 = **60%**

#### Recall@K (R@K)
$$\text{Recall@K} = \frac{\text{počet relevantných dokumentov v top K}}{\text{celkový počet relevantných v poole}}$$

**Príklad:** Ak existuje 10 relevantných dokumentov a systém vrátil 3 z nich v top 5 → R@5 = 3/10 = **30%**

#### F1-Score
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

#### Overlap@K (zhoda medzi systémami)
$$\text{Overlap@K}(A, B) = \frac{|A_{top K} \cap B_{top K}|}{K} \times 100\%$$

#### Zero-Result Rate (ZRR)
$$\text{ZRR} = \frac{\text{počet queries s 0 výsledkami}}{\text{celkový počet queries}} \times 100\%$$

---

## 📊 Ground Truth Evaluation

### Metodológia vytvorenia Ground Truth

Na korektné vypočítanie Precision a Recall sme vytvorili **Ground Truth dataset** pomocou **pooling method** (TREC štýl):

1. **Pooling:** Zozbierali sme top 10 výsledkov z každého systému (S1, S2, L1, L2) pre každú query
2. **Anotácia:** Pre každý dokument v poole sme určili relevanciu pomocou sémantických kritérií
3. **Kritériá relevancie:** Dokument je relevantný ak jeho názov obsahuje kľúčové termy query

**Príklad kritérií:**
- `italian sausage soup` → relevantné ak názov obsahuje "sausage"
- `mexican beef tacos` → relevantné ak názov obsahuje "taco", "fajita", "burrito", "enchilada"
- `vegan chocolate mousse` → relevantné ak názov obsahuje "mousse" alebo "vegan chocolate"

### Precision@5 a Recall@5 s Ground Truth

| # | Query | Pool | S1 P@5 | S1 R@5 | S2 P@5 | S2 R@5 | L1 P@5 | L1 R@5 | L2 P@5 | L2 R@5 |
|---|-------|------|--------|--------|--------|--------|--------|--------|--------|--------|
| 1 | `italian sausage soup` | 18 | **100%** | 28% | 20% | 6% | **100%** | 28% | **100%** | 28% |
| 2 | `mexican beef tacos` | 21 | **100%** | 24% | **100%** | 24% | 60% | 14% | **100%** | 24% |
| 3 | `thai peanut noodles` | 16 | 80% | 25% | **100%** | 31% | 60% | 19% | 40% | 12% |
| 4 | `keto friendly meatballs` | 15 | 40% | 13% | 0% | 0% | **100%** | 33% | **100%** | 33% |
| 5 | `creamy garlic shrimp pasta` | 22 | **100%** | 23% | **100%** | 23% | **100%** | 23% | 80% | 18% |
| 6 | `low carb cheesecake` | 7 | **60%** | **43%** | 40% | 29% | 20% | 14% | 0% | 0% |
| 7 | `pan fried pork chops` | 23 | **100%** | 22% | 20% | 4% | **100%** | 22% | **100%** | 22% |
| 8 | `vegan chocolate mousse` | 9 | 60% | 33% | 20% | 11% | 80% | 44% | **100%** | **56%** |
| 9 | `gluten free brownies` | 11 | **100%** | **45%** | **100%** | **45%** | 0% | 0% | 20% | 9% |
| 10 | `grilled vegetables marinade` | 13 | **100%** | **38%** | 60% | 23% | 40% | 15% | 80% | 31% |
|---|-------|------|--------|--------|--------|--------|--------|--------|--------|--------|
| | **PRIEMER** | | **84%** | **29%** | **56%** | **20%** | **66%** | **21%** | **72%** | **23%** |

### 📈 Súhrnné metriky

| Systém | Mean P@5 | Mean R@5 | F1-Score |
|--------|----------|----------|----------|
| 🥇 **S1 (Simple BM25)** | **84%** | **29%** | **44%** |
| 🥈 **L2 (Lucene TF-IDF)** | 72% | 23% | **35%** |
| 🥉 **L1 (Lucene BM25)** | 66% | 21% | 32% |
| 4. **S2 (Simple TF-IDF)** | 56% | 20% | 29% |

### 🔍 Detailný príklad výpočtu Precision@5 a Recall@5

#### Query: `italian sausage soup`

**Ground Truth Pool (18 relevantných dokumentov):**
1. Lentil Soup With Italian Sausage
2. Italian Sausage Soup
3. Italian (Turkey) Sausage Soup
4. Italian Sausage and Vegetable Saute
5. Italian Stuffed Beef & Sausage Bell Peppers
6. Spaghetti Bolognese Sauce (Beef and Italian Sausage)
7. Italian Sausage With Fusilli
8. Baked Rice With Sausage
9. Italian Sausage and Beef Stew
10. Italian Style Chicken, Sausage & Potato Bake
... a ďalších 8

**S1 (Simple BM25) - Top 5:**
| Rank | Dokument | Relevantný? |
|------|----------|-------------|
| 1 | Lentil Soup With Italian Sausage | ✅ |
| 2 | Italian Sausage Soup | ✅ |
| 3 | Italian (Turkey) Sausage Soup | ✅ |
| 4 | Italian Sausage and Vegetable Saute | ✅ |
| 5 | Italian Stuffed Beef & Sausage Bell Peppers | ✅ |

**Výpočet:**
$$\text{Precision@5} = \frac{5 \text{ relevantných}}{5} = \mathbf{100\%}$$
$$\text{Recall@5} = \frac{5 \text{ relevantných v top 5}}{18 \text{ relevantných v poole}} = \mathbf{28\%}$$

#### Query: `gluten free brownies`

**Ground Truth Pool (11 relevantných dokumentov):**
- Adzuki Bean Brownies (Gluten-Free, Vegan)
- Fudgy Salty Peanut Butter Brownies
- Chocolate Walnut Brownies
- King Arthur Flour's Best Fudge Brownies
- Peppermint Brownies
... a ďalších 6

**L1 (Lucene BM25) - Top 5:**
| Rank | Dokument | Relevantný? |
|------|----------|-------------|
| 1 | Gluten Free Brown Gravy | ❌ (nie brownie) |
| 2 | Sweet Shortcrust Pastry - GF | ❌ |
| 3 | Vanilla Sponge Cake - GF | ❌ |
| 4 | Thai Chicken Noodle Salad (GF) | ❌ |
| 5 | Gluten Free Corn Dogs | ❌ |

**Výpočet:**
$$\text{Precision@5} = \frac{0 \text{ relevantných}}{5} = \mathbf{0\%}$$
$$\text{Recall@5} = \frac{0}{11} = \mathbf{0\%}$$

**Poznámka:** L1 vrátil "gluten free" recepty, ale nie "brownies" - to je problém full-text vyhľadávania.

---

## 🔍 Analýza Overlap medzi systémami
| **L1** | Tacos De Pollo | Easy Tacos | Mexican Steak Casserole | Mexican Manicotti | Low Cal Beef Taco Soup |
| **L2** | Easy Tacos | Mexican Beef Skillet | Tacos De Pollo | Slow Cooker Mexican Beef Stew | Machaca (Mexican...) |
| **FC** | ❌ *0 výsledkov* | - | - | - | - |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **0%** | **20%** | 0% |
| **S2** | 0% | 100% | 0% | **20%** |
| **L1** | 20% | 0% | 100% | **40%** |
| **L2** | 0% | 20% | 40% | 100% |

**Zhodné dokumenty:**
- S1 ∩ L1: `Tacos De Pollo` (1/5 = 20%)
- S2 ∩ L2: `Slow Cooker Mexican Beef Stew` (1/5 = 20%)
- L1 ∩ L2: `Tacos De Pollo`, `Easy Tacos` (2/5 = 40%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| Všetky | **N/A** | Food.com vrátil 0 výsledkov |

**🏆 Víťaz: NÁŠ SYSTÉM** (Food.com zlyhal)

---

### 2. `thai peanut noodles` 🍜

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Thai Chicken Noodle Salad | King Du Noodles | Thai Salad Rolls | Tom Yum Goong | Robin Miller's Thai Salad |
| **S2** | Tom Yum Goong | Thai Mango Salad | Thai-curried Game Hens | Basic Thai Sweet Chili Sauce | Thai Red Rice Pudding |
| **L1** | Robin Miller's Thai Salad | Oodle Noodles | Thai Mango Salad | Thai Salad Rolls | Butterscotch Haystacks |
| **L2** | Thai Peanut Sauce | Thai Peanut Coconut Chicken | Parmesan Noodles | Oodle Noodles | Sesame Noodles |
| **FC** | Spicy Thai Peanut Noodles | Thai Peanut Noodles | Magic Noodles | Thai Veggie Peanut Noodles | Thai Peanut Noodles |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **40%** | 0% |
| **S2** | 20% | 100% | **20%** | 0% |
| **L1** | 40% | 20% | 100% | **20%** |
| **L2** | 0% | 0% | 20% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Tom Yum Goong` (20%)
- S1 ∩ L1: `Thai Salad Rolls`, `Robin Miller's Thai Salad` (40%)
- S2 ∩ L1: `Thai Mango Salad` (20%)
- L1 ∩ L2: `Oodle Noodles` (20%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Zhodné recepty |
|--------|-----------|----------------|
| S1 | **0%** | - |
| S2 | **0%** | - |
| L1 | **0%** | - |
| L2 | **~20%** | `Thai Peanut Sauce` (čiastočná zhoda s "Thai Peanut Noodles") |

**🏆 Víťaz: FOOD.COM** (presné názvy "Thai Peanut Noodles")

---

### 3. `keto friendly meatballs` 🍖

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Easy & Kid Friendly Sweet... | Macaroni and Cheese- Freezer | The Best Friends Granola Bar | Kittencal's Honey-Garlic Meatballs | Tailgate Grape Jelly Meatballs |
| **S2** | Beef Stewed in Red Pepper | Burrito Filling | Ketjap Manis | Easy & Kid Friendly Sweet... | Pesto |
| **L1** | Tailgate Grape Jelly Meatballs | Bavarian Meatballs | Kittencal's Honey-Garlic Meatballs | Chile Verde Meatballs | Easy Crockpot Meatballs |
| **L2** | Bavarian Meatballs | Tailgate Grape Jelly Meatballs | Chicago Meatballs | Frito Meatballs | Waikiki Meatballs |
| **FC** | ❌ *0 výsledkov* | - | - | - | - |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **40%** | **20%** |
| **S2** | 20% | 100% | 0% | 0% |
| **L1** | 40% | 0% | 100% | **40%** |
| **L2** | 20% | 0% | 40% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Easy & Kid Friendly Sweet...` (20%)
- S1 ∩ L1: `Kittencal's Honey-Garlic Meatballs`, `Tailgate Grape Jelly Meatballs` (40%)
- S1 ∩ L2: `Tailgate Grape Jelly Meatballs` (20%)
- L1 ∩ L2: `Bavarian Meatballs`, `Tailgate Grape Jelly Meatballs` (40%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| Všetky | **N/A** | Food.com vrátil 0 výsledkov |

**🏆 Víťaz: NÁŠ SYSTÉM** (Lucene indexy vrátili 5 meatball receptov)

---

### 4. `creamy garlic shrimp pasta` 🍝

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Shrimp and Angel Hair Pasta | Shrimp and Pasta in Tomato-Chile | Orange Shrimp Scampi | Pasta With Spinach, Nutmeg | Walley's Shrimp Scampi |
| **S2** | Tom Yum Goong | Walley's Shrimp Scampi | Parmesan Shrimp Au Gratin | Tilapia With Creamy Shrimp | Shrimp Scampi with Spaghetti |
| **L1** | Mushroom Pasta Scampi | Shrimp and Angel Hair Pasta | Garlic Shrimp and Grits | Shrimp Oreganato | Walley's Shrimp Scampi |
| **L2** | Garlic Shrimp and Grits | Shrimp and Angel Hair Pasta | Spicy Shrimp and Pasta | Garlic Chicken Pasta Primavera | Shrimp Oreganato |
| **FC** | Way-Easy Creamy Garlic Shrimp Pasta | Quick and Easy Creamy Garlic Shrimp Pasta | - | - | - |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **40%** | **20%** |
| **S2** | 20% | 100% | **20%** | 0% |
| **L1** | 40% | 20% | 100% | **60%** |
| **L2** | 20% | 0% | 60% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Walley's Shrimp Scampi` (20%)
- S1 ∩ L1: `Shrimp and Angel Hair Pasta`, `Walley's Shrimp Scampi` (40%)
- S1 ∩ L2: `Shrimp and Angel Hair Pasta` (20%)
- S2 ∩ L1: `Walley's Shrimp Scampi` (20%)
- L1 ∩ L2: `Shrimp and Angel Hair Pasta`, `Garlic Shrimp and Grits`, `Shrimp Oreganato` (60%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| S1 | **0%** | Sémanticky podobné (shrimp + pasta) |
| S2 | **0%** | Sémanticky podobné |
| L1 | **0%** | Sémanticky podobné (garlic shrimp) |
| L2 | **0%** | **Najlepšia sémantická zhoda** (Garlic Shrimp) |

**🏆 Víťaz: REMÍZA** (Food.com má presné názvy, náš systém má vysokú sémantickú relevanciu)

---

### 5. `low carb cheesecake` 🍰

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Guilt Free Low Cal Pumpkin Cheesecake | Low Carb-One Minute Chocolate | Pond Scum Soup(Low Carb) | Cheesecake Factory's Oreo Dream | Ww Fast Strawberry Cheesecake |
| **S2** | Low Carb-One Minute Chocolate | Swirled Cranberry Cheesecake | Low Carb Chili | Low Carb Peanut Dipping Sauce | Triple Chocolate Cheesecake |
| **L1** | Low Carb Peanut Dipping Sauce | Low Carb Chicken Casserole | Guilt Free Low Cal Pumpkin Cheesecake | Low Carb Hungarian Goulash | Low-Carb Spaghetti Squash |
| **L2** | Low Carb Chili | Low Carb Pasta | Low Carb Chicken Casserole | Low Carb Peanut Dipping Sauce | Low Carb Hungarian Goulash |
| **FC** | Low-Carb Cheesecake ⭐(69) | Super Simple Low Carb No-Bake ⭐(32) | Low Carb Cheesecake No Crust | Mackie's Low Carb/Sugar Free | Low Carb Mini Cheesecakes |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **20%** | 0% |
| **S2** | 20% | 100% | **20%** | **40%** |
| **L1** | 20% | 20% | 100% | **60%** |
| **L2** | 0% | 40% | 60% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Low Carb-One Minute Chocolate` (20%)
- S1 ∩ L1: `Guilt Free Low Cal Pumpkin Cheesecake` (20%)
- S2 ∩ L1: `Low Carb Peanut Dipping Sauce` (20%)
- S2 ∩ L2: `Low Carb Chili`, `Low Carb Peanut Dipping Sauce` (40%)
- L1 ∩ L2: `Low Carb Peanut Dipping Sauce`, `Low Carb Chicken Casserole`, `Low Carb Hungarian Goulash` (60%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Zhodné recepty |
|--------|-----------|----------------|
| S1 | **~20%** | `Guilt Free Low Cal Pumpkin Cheesecake` (podobné) |
| S2 | **0%** | - |
| L1 | **~20%** | `Guilt Free Low Cal Pumpkin Cheesecake` |
| L2 | **0%** | - |

**🏆 Víťaz: FOOD.COM** (51 presných "Low Carb Cheesecake" výsledkov)

---

### 6. `pan fried pork chops` 🥩

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Pork Chops With Goat Cheese | Pork chops and peppers | Pork Chops With Apples and Raisins | Easy, Crunchy Pork Chops | Pork Chops With Apples and Onion |
| **S2** | Baked Ranch Chops | Hoisin Pork Chops | Loaded Baked Potato Soup | Spinach Stuffed Chicken | Spinach-Poblano Enchiladas |
| **L1** | Pork Chops | Stuffed Pork Chops | Tasty Brown Sugar Pork Chops | Smoked Pork Chops | Pineapple Garlic Pork Chops |
| **L2** | Pork Chops | Stuffed Pork Chops | Smoked Pork Chops | Glazed Pork Chops | Tasty Brown Sugar Pork Chops |
| **FC** | Pan Fried Pork Chops ⭐(13) | Southern Pan Fried Pork Chops | Luccas's Pan Fried Pork Chops | South West Pan Fried Pork Chops | Pan Fried Pork Chops and Homemade... |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | 0% | 0% | 0% |
| **S2** | 0% | 100% | 0% | 0% |
| **L1** | 0% | 0% | 100% | **80%** |
| **L2** | 0% | 0% | 80% | 100% |

**Zhodné dokumenty:**
- L1 ∩ L2: `Pork Chops`, `Stuffed Pork Chops`, `Smoked Pork Chops`, `Tasty Brown Sugar Pork Chops` (80%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| S1 | **0%** | 5/5 pork chops, ale nie "Pan Fried" |
| S2 | **0%** | Žiadne pork chops |
| L1 | **0%** | 5/5 pork chops, ale nie "Pan Fried" |
| L2 | **0%** | 5/5 pork chops, ale nie "Pan Fried" |

**🏆 Víťaz: REMÍZA** (Food.com má presné "Pan Fried", náš má vysoký počet pork chops)

---

### 7. `vegan chocolate mousse` 🍫

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Vegan Heart Attack Chocolate Doughnuts | Gordon Ramsay Chocolate Mousse | Easy Vegan Ravioli | Vegan Cowboy Cookies | Oreo Chocolate Mousse |
| **S2** | Easy Vegan Ravioli | Favorite Vegan Chili | Vegan Heart Attack Chocolate | Vegan Banana Crumble | Vegan Shepherd's Pie |
| **L1** | Gordon Ramsay Chocolate Mousse | Chocolate Raspberry Cake | Blender Chocolate Mousse | Oreo Chocolate Mousse | Chocolate Banana Strawberry Mousse |
| **L2** | Blender Chocolate Mousse | Gordon Ramsay Chocolate Mousse | Oreo Chocolate Mousse | Chocolate Peanut Butter Mousse | Chocolate Banana Strawberry Mousse |
| **FC** | Vegan Chocolate Mousse ⭐(4) | Vegan Chocolate Chilli Pepper | Vegan Chocolate Mousse | Raw Vegan Chocolate Cinnamon... | Vegan Chocolate Orange Mousse |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **40%** | **20%** |
| **S2** | 20% | 100% | 0% | 0% |
| **L1** | 40% | 0% | 100% | **80%** |
| **L2** | 20% | 0% | 80% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Easy Vegan Ravioli` alebo `Vegan Heart Attack Chocolate` (20%)
- S1 ∩ L1: `Gordon Ramsay Chocolate Mousse`, `Oreo Chocolate Mousse` (40%)
- S1 ∩ L2: `Oreo Chocolate Mousse` (20%)
- L1 ∩ L2: `Gordon Ramsay Chocolate Mousse`, `Blender Chocolate Mousse`, `Oreo Chocolate Mousse`, `Chocolate Banana Strawberry Mousse` (80%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| S1 | **0%** | Má mousse, ale nie vegan mousse |
| S2 | **0%** | Má vegan, ale nie mousse |
| L1 | **0%** | 4/5 chocolate mousse (nie vegan) |
| L2 | **0%** | 5/5 chocolate mousse (nie vegan) |

**🏆 Víťaz: FOOD.COM** (presné "Vegan Chocolate Mousse")

---

### 8. `gluten free brownies` 🍪

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Adzuki Bean Brownies (GF, Vegan) | Fudgy Salty Peanut Butter Brownies | Chocolate Walnut Brownies | King Arthur Flour's Fudge Brownies | Peppermint Brownies |
| **S2** | Rehab Brownies | King Arthur Flour's Fudge Brownies | Chocolate Walnut Brownies | Quadruple Chocolate Brownies | Peppermint Brownies |
| **L1** | Gluten Free Brown Gravy | Sweet Shortcrust Pastry - GF | Vanilla Sponge Cake - GF | Thai Chicken Noodle Salad (GF) | Gluten Free Corn Dogs |
| **L2** | Gluten Free Brown Gravy | Sweet Shortcrust Pastry - GF | Gluten Free Corn Dogs | Adzuki Bean Brownies (GF, Vegan) | Gluten Free Oatmeal Raisin Cookies |
| **FC** | Gluten-Free Cocoa Brownies ⭐(14) | Pamela's Gluten-Free Brownies ⭐(11) | Gluten Free Chocolate Chip Brownies | Gluten-Free Walnut Brownies | Decadent Gluten Free Vegan Brownies |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **60%** | 0% | **20%** |
| **S2** | 60% | 100% | 0% | 0% |
| **L1** | 0% | 0% | 100% | **60%** |
| **L2** | 20% | 0% | 60% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Chocolate Walnut Brownies`, `King Arthur Flour's Fudge Brownies`, `Peppermint Brownies` (60%)
- S1 ∩ L2: `Adzuki Bean Brownies (GF, Vegan)` (20%)
- L1 ∩ L2: `Gluten Free Brown Gravy`, `Sweet Shortcrust Pastry - GF`, `Gluten Free Corn Dogs` (60%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| S1 | **20%** | `Adzuki Bean Brownies (GF, Vegan)` = GF brownie ✅ |
| S2 | **0%** | Brownies, ale nie gluten-free |
| L1 | **0%** | GF recepty, ale nie brownies |
| L2 | **20%** | `Adzuki Bean Brownies (GF, Vegan)` = GF brownie ✅ |

**🏆 Víťaz: FOOD.COM** (30 presných gluten-free brownies)

---

### 9. `grilled vegetables marinade` 🥗

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Grilled Portabella w/ Balsamic Marinade | Grilled Shoulder Lamb Chops w/ Marinade | Chipotle Marinade for Grilled Chicken | Sirloin Steak Tips w/ Soy Marinade | Flank Steak With Lemon Shallot Marinade |
| **S2** | Anticuchos (Peruvian Beef) | Vietnamese Rice Noodle Salad | Sirloin Steak Tips w/ Soy Marinade | Lower-carb Teriyaki Marinade | Polynesian Marinade |
| **L1** | Grilled Portabella w/ Balsamic Marinade | Chipotle Marinade for Grilled Chicken | Teriyaki Chicken | Cajun Grilled Shrimp | Salmon (Microwave-Cooked) |
| **L2** | Chipotle Marinade for Grilled Chicken | Grilled Portabella w/ Balsamic Marinade | Vegetables Supreme | Grilled Tuna & Vegetables | Shrimp Marinade |
| **FC** | ❌ *0 výsledkov* | - | - | - | - |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | **20%** | **40%** | **40%** |
| **S2** | 20% | 100% | 0% | 0% |
| **L1** | 40% | 0% | 100% | **40%** |
| **L2** | 40% | 0% | 40% | 100% |

**Zhodné dokumenty:**
- S1 ∩ S2: `Sirloin Steak Tips w/ Soy Marinade` (20%)
- S1 ∩ L1: `Grilled Portabella w/ Balsamic Marinade`, `Chipotle Marinade for Grilled Chicken` (40%)
- S1 ∩ L2: `Grilled Portabella w/ Balsamic Marinade`, `Chipotle Marinade for Grilled Chicken` (40%)
- L1 ∩ L2: `Grilled Portabella w/ Balsamic Marinade`, `Chipotle Marinade for Grilled Chicken` (40%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Poznámka |
|--------|-----------|----------|
| Všetky | **N/A** | Food.com vrátil 0 výsledkov |

**🏆 Víťaz: NÁŠ SYSTÉM** (Food.com zlyhal)

---

### 10. `italian sausage soup` 🍲

| Systém | #1 | #2 | #3 | #4 | #5 |
|--------|----|----|----|----|-----|
| **S1** | Lentil Soup With Italian Sausage | **Italian Sausage Soup** ✅ | Italian (Turkey) Sausage Soup | Italian Sausage and Vegetable Saute | Italian Stuffed Beef & Sausage |
| **S2** | Baked Italian Heros | Meaty Mostaccioli | Orecchiette With Broccoli Rabe | Polpette Alla Casalinga | Italian Ziti Medley |
| **L1** | **Italian Sausage Soup** ✅ | Lentil Soup With Italian Sausage | Sausage Scaloppine | Italian (Turkey) Sausage Soup | Italian Style Chicken Sausage |
| **L2** | **Italian Sausage Soup** ✅ | Italian (Turkey) Sausage Soup | Italian Sausage & Potatoes | Italian Sausage Meatballs | Lentil Soup With Italian Sausage |
| **FC** | Italian Sausage Vegetable Soup ⭐(124) | **Italian Sausage Soup** ⭐(25) | Italian Sausage Crockpot Soup | **Italian Sausage Soup** ⭐(8) | Italian (Turkey) Sausage Soup |

#### 📊 Matica zhody Overlap@5 (naše systémy)

|  | S1 | S2 | L1 | L2 |
|--|----|----|----|----|
| **S1** | 100% | 0% | **60%** | **40%** |
| **S2** | 0% | 100% | 0% | 0% |
| **L1** | 60% | 0% | 100% | **60%** |
| **L2** | 40% | 0% | 60% | 100% |

**Zhodné dokumenty:**
- S1 ∩ L1: `Lentil Soup With Italian Sausage`, `Italian Sausage Soup`, `Italian (Turkey) Sausage Soup` (60%)
- S1 ∩ L2: `Italian Sausage Soup`, `Italian (Turkey) Sausage Soup` (40%)
- L1 ∩ L2: `Italian Sausage Soup`, `Italian (Turkey) Sausage Soup`, `Lentil Soup With Italian Sausage` (60%)

#### 🆚 Zhoda s Food.com
| Systém | Zhoda s FC | Zhodné recepty |
|--------|-----------|----------------|
| S1 | **40%** | `Italian Sausage Soup` ✅, `Italian (Turkey) Sausage Soup` ✅ |
| S2 | **0%** | - |
| L1 | **40%** | `Italian Sausage Soup` ✅, `Italian (Turkey) Sausage Soup` ✅ |
| L2 | **40%** | `Italian Sausage Soup` ✅, `Italian (Turkey) Sausage Soup` ✅ |

**🏆 Víťaz: REMÍZA** (Oba systémy majú "Italian Sausage Soup")

---

## 📊 Súhrnná štatistika

### Celková matica priemernej zhody Overlap@5

|  | S1 | S2 | L1 | L2 | FC |
|--|----|----|----|----|-----|
| **S1** | - | **18%** | **30%** | **18%** | 8% |
| **S2** | 18% | - | **8%** | **8%** | 0% |
| **L1** | 30% | 8% | - | **54%** | 10% |
| **L2** | 18% | 8% | 54% | - | 12% |
| **FC** | 8% | 0% | 10% | 12% | - |

### 🔑 Kľúčové zistenia o zhode

| Porovnanie | Priemerná zhoda | Interpretácia |
|------------|-----------------|---------------|
| **L1 ↔ L2** | **54%** | 🟢 Najvyššia zhoda - rovnaký Lucene engine |
| **S1 ↔ L1** | **30%** | 🟡 Stredná zhoda - rovnaká metrika (BM25) |
| **S1 ↔ S2** | **18%** | 🔴 Nízka zhoda - rôzne metriky |
| **S1 ↔ L2** | **18%** | 🔴 Nízka zhoda |
| **Náš ↔ FC** | **~8%** | 🔴 Veľmi nízka - rôzne prístupy |

### Zero-Result Rate (ZRR)

| Systém | Queries s 0 výsledkami | ZRR |
|--------|----------------------|-----|
| **S1, S2, L1, L2** | 0 / 10 | **0%** |
| **Food.com** | 3 / 10 | **30%** |

### Finálne hodnotenie systémov

```
┌────────────────────────────────────────────────────────────────────┐
│           FINÁLNE HODNOTENIE (s Ground Truth metrikami)           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  🥇 1. SIMPLE BM25 (S1)                                           │
│     • Mean Precision@5: 84%                                       │
│     • Mean Recall@5: 29%                                          │
│     • F1-Score: 44%                                               │
│     • ZRR: 0%                                                     │
│                                                                    │
│  🥈 2. LUCENE TF-IDF (L2)                                         │
│     • Mean Precision@5: 72%                                       │
│     • Mean Recall@5: 23%                                          │
│     • F1-Score: 35%                                               │
│     • ZRR: 0%                                                     │
│                                                                    │
│  🥉 3. LUCENE BM25 (L1)                                           │
│     • Mean Precision@5: 66%                                       │
│     • Mean Recall@5: 21%                                          │
│     • F1-Score: 32%                                               │
│     • ZRR: 0%                                                     │
│                                                                    │
│  4. SIMPLE TF-IDF (S2)                                            │
│     • Mean Precision@5: 56%                                       │
│     • Mean Recall@5: 20%                                          │
│     • F1-Score: 29%                                               │
│     • ZRR: 0%                                                     │
│                                                                    │
│  5. FOOD.COM (FC)                                                 │
│     • ZRR: 30% ⚠️ (3/10 queries bez výsledkov)                    │
│     • Tag-based systém zlyháva na frázach                         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Závery

### Čo sme zistili s Ground Truth metrikami

1. **Simple BM25 (S1) je najlepší** s Mean P@5 = 84% a F1 = 44%
2. **Lucene TF-IDF (L2)** je druhý najlepší s P@5 = 72%
3. **Lucene indexy sú najkonzistentnejšie** - 54% Overlap@5 medzi sebou
4. **Food.com má problém so ZRR** - 30% queries bez výsledkov

### Prečo S1 vyhráva?

Simple BM25 implementácia má **lepšiu tokenizáciu a normalizáciu** pre multi-term queries. Lucene BM25 síce má sofistikovanejšiu matematiku, ale naša jednoduchá implementácia lepšie zachytáva sémantickú relevanciu.

### Odporúčanie

Pre produkčné nasadenie odporúčame **Simple BM25 (S1)** kvôli:
- Najvyššej Precision@5 (84%)
- Najvyššiemu F1-Score (44%)
- Nulovému zero-result rate

Alternatívne **Lucene TF-IDF (L2)** ak je potrebná vyššia konzistencia a štandardná implementácia.

---

**Vytvorené:** 09. December 2025  
**Ground Truth:** 10 queries, pooling method, automatická anotácia relevancie
