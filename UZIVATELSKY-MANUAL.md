---
type: notes
title: "Uživatelský manuál"
status: active
summary: "Tenhle Pack je hotové, bezpečné nastavení pro **Claude Code (CC)** - terminálovou appku od Anthropic, která ti reálně dělá věci na počítači: píše soubory, spouští příkazy, umí nainstalovat skoro cokol"
created: 2026-06-13
updated: 2026-06-13
created_by: Šimon Hradní
client: ~
path: UZIVATELSKY-MANUAL.md
tags: [note]
---

# Uživatelský manuál

Tenhle Pack je hotové, bezpečné nastavení pro **Claude Code (CC)** - terminálovou appku od Anthropic, která ti reálně dělá věci na počítači: píše soubory, spouští příkazy, umí nainstalovat skoro cokoliv. Pack ho nastaví tak, aby ti omylem nesmazal data nebo nesahal na citlivé věci, a přidá pár nástrojů, co se hodí při běžné práci.

Je stavěný pro **ambasadory a power-usery** - lidi, co píšou drobné skripty, stavějí s Claude Code malé appky a dělají znalostní práci. Nemusíš být vývojář.

## Než půjdeš dál

**Claude Code není chat.** Na claude.ai napíšeš zprávu, dostaneš odpověď a na disku se nic neděje. V Claude Code zadáš úkol a Claude **fakt** edituje soubory, spouští příkazy, instaluje věci. Tenhle Pack je pojistka, aby to nedopadlo špatně.

## Co s tím budeš dělat

- **Zadávat úkoly normálně, česky.** „Projdi tyhle přepisy a vytáhni úkoly", „udělej mi z téhle tabulky přehled", „naskriptuj stažení reportů". Claude to udělá u tebe na počítači.
- **Zakládat projekty přes `/setup`.** Pro každého klienta nebo vlastní projekt napíšeš `/setup` a Claude ti připraví složky a šablony - ale nejdřív se tě zeptá, jak to chceš mít. Strukturu bere jako návrh, ne jako něco napevno.
- **Mít přehled o spotřebě.** Statusbar dole ukazuje, kolik z týmového limitu projídáš (5h i 7denní okno), stav kontextu a cenu session.
- **Hlídat data klientů.** Skill `client-data-check` ti projede soubor a najde v něm citlivé/osobní údaje dřív, než ho někam pošleš.

## Instalace

Odkaz na tohle repo dej do Claude Code a řekni mu, ať si to načte a postupuje podle `INSTRUCTIONS.md`.

Claude tě provede nastavením otázku po otázce. **Každý krok schvaluješ ty.** Když už nějaké nastavení máš, Claude ho **nepřepíše** - zazálohuje ho, podívá se, co tam máš, porovná s Packem a **doporučí ti, jak to upravit na míru tobě**.

## Pět věcí, které si zapamatuj

1. **Čti plán, než řekneš „ano".** Většina chyb vzniká z odsouhlasení nepřečteného plánu.
2. **Když Claude něco nesmí, neobcházej to.** Řekni mu cíl, ne work-around. Navrhne bezpečnější cestu, nebo ti dá příkaz ke spuštění ručně.
3. **API klíče a tokeny dej do `~/.claude/.env`.** Claude do hodnot nevidí, pracuje jen s názvy klíčů. Když mu nějaký klíč reálně potřebuješ dát, je na to soubor `.env.local` v daném projektu.
4. **Statusbar dole čti.** Hlavně stav kontextu a kolik z týmového limitu jedeš.
5. **Nový projekt = `/setup`.** Připraví složky a šablony, předtím se doptá, jak to chceš mít ty.

## Když něco nejde

| Situace | Co dělat |
|---------|----------|
| Claude opakuje stejnou chybu | Ukonči (`Ctrl+D`), spusť novou session |
| Statusbar svítí červeně | Pauza, nebo úkol dodělej na claude.ai |
| Claude chce dělat něco divného | Zeptej se: *„Co přesně chceš udělat? Ještě to nedělej."* |
| Po instalaci nevidím staré nastavení | Není pryč, záloha je v `~/.claude.bak-<datum>/` |

## Kam dál

- **`README.md`** - co Pack obsahuje a v čem se liší od základní verze
- **`INSTRUCTIONS.md`** - instalační skript pro Claude (ty ho nečteš, čte ho on)

## O autorovi

Tenhle Pack jsem postavil já, **Šimon Hradní** - průvodce AI. Pomáhám firmám a týmům reálně používat AI v denní práci, bez hype a buzzwordů.

Když tě zajímá víc - Claude Code, AI nástroje, AI v agentuře nebo ve firmě obecně - ozvi se:

- simon@hradni.net
- [linkedin.com/in/simonhradni](https://linkedin.com/in/simonhradni)
