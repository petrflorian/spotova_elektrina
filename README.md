# Spotová Elektřina pro Home Assistant

Integrace pro sledování spotových cen elektřiny z webu spotovaelektrina.cz

## Instalace

### HACS (doporučeno)

1. Přidejte tento repozitář do HACS jako Custom Repository:
   - Otevřete HACS
   - Klikněte na tři tečky vpravo nahoře
   - Vyberte "Custom repositories"
   - Přidejte URL: `https://github.com/petrflorian/spotova_elektrina`
   - Kategorie: Integration
2. Klikněte na "Spotová Elektřina" a poté na "DOWNLOAD"
3. Restartujte Home Assistant

### Manuální instalace

1. Stáhněte si obsah tohoto repozitáře
2. Zkopírujte složku `custom_components/spotova_elektrina` do vaší instalace Home Assistant
3. Restartujte Home Assistant

## Nastavení

1. Přejděte do Nastavení -> Zařízení a služby
2. Klikněte na tlačítko "+ PŘIDAT INTEGRACI"
3. Vyhledejte "Spotová Elektřina"

## Zobrazení dat

Zobrazení aktualní ceny a cen na příštích 6 hodin


sensor.spotova_elektrina_aktualni
sensor.spotova_elektrina_1h
sensor.spotova_elektrina_2h
sensor.spotova_elektrina_3h
sensor.spotova_elektrina_4h
sensor.spotova_elektrina_5h
sensor.spotova_elektrina_6h



Pro zobrazení tabulky s cenami můžete použít následující kartu v Lovelace:

```yaml
type: markdown
title: Cena elektřiny dnes
content: |
  | Hodina | Cena |
  |--------|------|
  {% for hour, price in state_attr('sensor.spotova_elektrina', 'forecast_today').items() %}
  | {{ hour }} | {{ price }} Kč |
  {% endfor %}
```


Pro zobrazení aktualní ceny a cen na příštích 6 hodin
```yaml
  type: vertical-stack
cards:
  - type: entity
    name: "Aktuální cena"
    entity: sensor.spotova_elektrina
    
  - type: markdown
    title: "Následující hodiny"
    content: |
      {% set current_hour = now().hour %}
      {% set hours = namespace(list=[]) %}
      {% for i in range(6) %}
        {% set next_hour = (current_hour + i + 1) % 24 %}
        {% set hours.list = hours.list + [next_hour] %}
      {% endfor %}

      | Hodina | Cena |
      |--------|------|
      {% for hour in hours.list -%}
      | {{ '%02d'|format(hour) }}:00 | {{ state_attr('sensor.spotova_elektrina', 'forecast_today')['%02d:00'|format(hour)] }} Kč |
      {% endfor %}

```