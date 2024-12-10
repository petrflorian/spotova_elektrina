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