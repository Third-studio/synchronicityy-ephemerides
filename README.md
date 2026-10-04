# Éphémérides par maison

Deux petits programmes de calcul astronomique, publiés sous licence [AGPL-3.0](LICENSE) parce qu'ils utilisent [Swiss Ephemeris](https://www.astro.com/swisseph/) (Astrodienst AG) via [pyswisseph](https://pypi.org/project/pyswisseph/).

- `ephemerides.py` : pour une naissance (date, heure, lieu) et une période, liste jour par jour les planètes en transit dans chacune des douze maisons natales (Placidus, maisons entières au-delà du cercle polaire), leurs rétrogradations, et les éclipses avec leur maison.
- `lunaisons.py` : nouvelles et pleines lunes d'une période, avec leur signe.

Ces programmes ne font que des calculs : ils n'interprètent rien.

```
pip install pyswisseph timezonefinder tzdata geopy
python3 ephemerides.py --date 1990-06-15 --heure 14:00 --lat 48.8566 --lon 2.3522 \
    --debut 2026-10-03 --jusqu-au 2027-01-02 --sortie ephemerides.json
python3 lunaisons.py --prochaine
```

Licence : GNU Affero General Public License v3.0. Swiss Ephemeris est distribué par Astrodienst AG sous double licence AGPL / Swiss Ephemeris Professional License.
