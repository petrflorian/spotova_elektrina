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

```yaml
sensor.spotova_elektrina_aktualni
sensor.spotova_elektrina_1h
sensor.spotova_elektrina_2h
sensor.spotova_elektrina_3h
sensor.spotova_elektrina_4h
sensor.spotova_elektrina_5h
sensor.spotova_elektrina_6h
```
