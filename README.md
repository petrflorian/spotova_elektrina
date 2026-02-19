# Spotová Elektřina pro Home Assistant

Vlastní integrace Home Assistantu pro načítání spotových cen elektřiny ze služby [spotovaelektrina.cz](https://spotovaelektrina.cz).

## Co integrace dělá

- načítá aktuální spotovou cenu elektřiny
- používá primárně **čtvrthodinová data (15 min)**
- vystavuje hlavní senzor + hodinové senzory `+1h` až `+6h`
- přidává čtvrthodinové senzory `+15m` až `+90m` pro jemnější zobrazení
- poskytuje přehled dnešních a zítřejších cen v atributech senzoru

## Důležitá změna od 1. 10. 2025

Od **1. října 2025** jsou spotové ceny na trhu čtvrthodinové.
Integrace proto používá endpoint:

- `https://spotovaelektrina.cz/api/v1/price/get-prices-json-qh`

Pokud je nový endpoint dočasně nedostupný, integrace má fallback na hodinové API:

- `https://spotovaelektrina.cz/api/v1/price/get-prices-json`

V takovém případě se v atributech projeví rozlišení `60` minut.

## Požadavky

- Home Assistant s podporou custom integrací
- HACS (doporučeno) nebo manuální kopie do `custom_components`
- přístup Home Assistantu na internet (volání API)

## Instalace

### Varianta A: HACS (doporučeno)

1. Otevři HACS.
2. `⋮` -> `Custom repositories`.
3. Přidej repozitář `https://github.com/petrflorian/spotova_elektrina`.
4. Typ: `Integration`.
5. Nainstaluj integraci `Spotová Elektřina`.
6. Restartuj Home Assistant.

### Varianta B: Manuálně

1. Zkopíruj složku `custom_components/spotova_elektrina` do Home Assistant konfigurace.
2. Restartuj Home Assistant.

## Konfigurace v Home Assistantu

1. `Nastavení` -> `Zařízení a služby`.
2. Klikni na `+ Přidat integraci`.
3. Vyhledej `Spotová Elektřina`.
4. Dokonči přidání.

Integrace je single-instance (pouze jedna konfigurace).

## Entity

Po instalaci vzniknou entity:

- `sensor.spotova_elektrina` (aktuální cena)
- `sensor.spotova_elektrina_15m`
- `sensor.spotova_elektrina_30m`
- `sensor.spotova_elektrina_45m`
- `sensor.spotova_elektrina_60m`
- `sensor.spotova_elektrina_75m`
- `sensor.spotova_elektrina_90m`
- `sensor.spotova_elektrina_1h`
- `sensor.spotova_elektrina_2h`
- `sensor.spotova_elektrina_3h`
- `sensor.spotova_elektrina_4h`
- `sensor.spotova_elektrina_5h`
- `sensor.spotova_elektrina_6h`

Všechny senzory mají jednotku `Kč/kWh`.

Poznámka: offset senzory (`+15m` až `+90m`, `+1h` až `+6h`) jsou
**ve výchozím stavu vypnuté**. Standardně tedy uvidíš jen hlavní senzor
`sensor.spotova_elektrina`. Pokud je chceš, zapneš je v registru entit.

## Atributy hlavního senzoru

`sensor.spotova_elektrina` vrací tyto důležité atributy:

- `resolution_minutes`: `15` nebo `60` (při fallbacku)
- `forecast_today`: mapování času na cenu (`HH:MM` -> `Kč/kWh`)
- `forecast_tomorrow`: mapování času na cenu (`HH:MM` -> `Kč/kWh`)

Při 15min datech má každý den obvykle 96 hodnot.

## Atributy offset senzorů (+15m až +90m, +1h až +6h)

Každý offset senzor obsahuje:

- `hour`: cílová hodina (`HH:00`)
- `slot`: cílový slot (`HH:MM`)
- `date`: cílové datum
- `resolution_minutes`: `15` nebo `60`
- `data_points_for_day`: počet dostupných slotů v daném dni

## Jak interpretovat data

- API vrací ceny v `Kč/MWh`.
- Integrace je převádí na `Kč/kWh` (`/1000`) a zaokrouhluje na 2 desetinná místa.
- U 15min dat se pro aktuální hodnotu používá právě běžící čtvrthodinový slot.

## Příklady použití

### Jednoduché zobrazení v kartě Entities

```yaml
type: entities
title: Spotová elektřina
entities:
  - entity: sensor.spotova_elektrina
  - entity: sensor.spotova_elektrina_15m
  - entity: sensor.spotova_elektrina_30m
  - entity: sensor.spotova_elektrina_45m
  - entity: sensor.spotova_elektrina_1h
  - entity: sensor.spotova_elektrina_2h
  - entity: sensor.spotova_elektrina_3h
```

### Template senzor: minimum z dnešního forecastu

```yaml
template:
  - sensor:
      - name: "Spot - dnešní minimum"
        unit_of_measurement: "Kč/kWh"
        state: >-
          {% set values = state_attr('sensor.spotova_elektrina', 'forecast_today') %}
          {% if values %}
            {{ values.values() | min }}
          {% else %}
            unknown
          {% endif %}
```

## Omezení

- Integrace neobsahuje distribuční složku ceny, DPH ani poplatky obchodníka.
- Hodnoty reprezentují spotovou cenu silové elektřiny z API poskytovatele.
- Kvalita a dostupnost dat je závislá na dostupnosti externího API.

## Řešení problémů

1. Ověř, že Home Assistant má internetové připojení.
2. Zkontroluj stav API endpointu v prohlížeči.
3. Restartuj Home Assistant po aktualizaci integrace.
4. Zkontroluj logy Home Assistantu (`Nastavení` -> `Systém` -> `Protokoly`).

Pro detailnější debug můžeš přidat do `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.spotova_elektrina: debug
```

## Vývoj a validace

Repozitář obsahuje workflow pro validaci přes Hassfest a HACS action.

## Licence

Projekt je licencován pod MIT licencí. Viz soubor `LICENSE`.
