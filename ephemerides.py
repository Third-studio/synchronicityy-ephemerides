"""Éphémérides par maison : quelles planètes occupent quelle maison natale, jour par jour.

Programme autonome, publié sous licence AGPL-3.0 (il utilise Swiss Ephemeris via pyswisseph).
Il ne fait que des calculs astronomiques : positions, rétrogradations, cuspides, éclipses.
Il n'interprète rien.

Usage :
  python3 ephemerides.py --date 1990-06-15 --heure 14:00 --lat 48.8566 --lon 2.3522 [--tz Europe/Paris] \
      --debut 2026-10-03 --jusqu-au 2027-11-15 [--eclipses-jusqu-au 2027-11-27] --sortie ephemerides.json
  (--lieu "Ville, Pays" peut remplacer --lat/--lon si geopy est installé.)

Sortie JSON :
  systeme_maisons, fuseau_naissance, decalage_naissance_utc, cuspides (12 longitudes),
  jours : {"AAAA-MM-JJ": {"1": [["Mars", false], ...], ..., "12": [...]}}  (à midi UTC)
  eclipses : [["AAAA-MM-JJ", "solaire"|"lunaire", maison], ...]
Mercure n'est listé que lorsqu'il est rétrograde ; Soleil et Lune ne sont pas listés ; Nœuds vrais.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

PLANETES = [("Vénus", swe.VENUS), ("Mars", swe.MARS), ("Jupiter", swe.JUPITER),
            ("Saturne", swe.SATURN), ("Uranus", swe.URANUS), ("Neptune", swe.NEPTUNE),
            ("Pluton", swe.PLUTO), ("Mercure", swe.MERCURY)]


def coordonnees(args):
    if args.lat is not None and args.lon is not None:
        return args.lat, args.lon
    if not args.lieu:
        raise SystemExit("Donner --lat et --lon, ou --lieu.")
    from geopy.geocoders import Nominatim  # import tardif : optionnel
    loc = Nominatim(user_agent="ephemerides-maisons").geocode(args.lieu)
    if not loc:
        raise SystemExit(f"Lieu introuvable : {args.lieu}. Donner --lat et --lon.")
    return loc.latitude, loc.longitude


def fuseau(lat, lon, tz):
    if tz:
        return tz
    from timezonefinder import TimezoneFinder
    nom = TimezoneFinder().timezone_at(lat=lat, lng=lon)
    if not nom:
        raise SystemExit("Fuseau introuvable pour ces coordonnées. Donner --tz (nom IANA).")
    return nom


def jour_julien_naissance(d, heure, tz):
    """Heure locale -> UTC avec l'historique du fuseau (heure d'été comprise)."""
    h, mn = (int(x) for x in heure.split(":"))
    local = datetime(d.year, d.month, d.day, h, mn, tzinfo=ZoneInfo(tz))
    u = local.astimezone(timezone.utc)
    off = local.utcoffset().total_seconds() / 3600
    signe = "+" if off >= 0 else "−"
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60), f"UTC{signe}{abs(int(off)):02d}:{int(abs(off) % 1 * 60):02d}"


def cuspides(jd, lat, lon):
    systeme = b"P" if abs(lat) < 66 else b"W"  # Placidus, maisons entières au-delà du cercle polaire
    c, _ = swe.houses(jd, lat, lon, systeme)
    return list(c[:12]), systeme.decode()


def maison_de(deg, c):
    for i in range(12):
        a, b = c[i], c[(i + 1) % 12]
        if (a <= deg < b) if a <= b else (deg >= a or deg < b):
            return i + 1
    return 12


def eclipses(debut, fin, c):
    res = []
    for fn, astre, nom in ((swe.sol_eclipse_when_glob, swe.SUN, "solaire"),
                           (swe.lun_eclipse_when, swe.MOON, "lunaire")):
        j = swe.julday(debut.year, debut.month, debut.day, 0) - 30
        for _ in range(40):
            t = fn(j)[1][0]
            y, m, d, _ = swe.revjul(t)
            jour = date(y, m, int(d))
            if jour > fin:
                break
            res.append((jour, nom, maison_de(swe.calc_ut(t, astre)[0][0], c)))
            j = t + 10
    return sorted(set(res))


def occupation(jour, c):
    o = {i: [] for i in range(1, 13)}
    j = swe.julday(jour.year, jour.month, jour.day, 12)
    for nom, p in PLANETES:
        x = swe.calc_ut(j, p)[0]
        rx = x[3] < 0
        if nom == "Mercure" and not rx:
            continue
        o[maison_de(x[0], c)].append((nom, rx))
    nn = swe.calc_ut(j, swe.TRUE_NODE)[0][0]
    o[maison_de(nn, c)].append(("Nœud Nord", False))
    o[maison_de((nn + 180) % 360, c)].append(("Nœud Sud", False))
    return o


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="AAAA-MM-JJ")
    p.add_argument("--heure", required=True, help="HH:MM, heure locale de naissance")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--lieu")
    p.add_argument("--tz", help="Nom IANA, ex. America/Guadeloupe")
    p.add_argument("--debut", required=True, help="AAAA-MM-JJ, premier jour")
    p.add_argument("--jusqu-au", required=True, help="AAAA-MM-JJ, dernier jour inclus")
    p.add_argument("--eclipses-jusqu-au", help="AAAA-MM-JJ, par défaut --jusqu-au")
    p.add_argument("--sortie", required=True)
    a = p.parse_args()

    lat, lon = coordonnees(a)
    tz = fuseau(lat, lon, a.tz)
    jd, decalage = jour_julien_naissance(date.fromisoformat(a.date), a.heure, tz)
    c, systeme = cuspides(jd, lat, lon)
    debut, fin = date.fromisoformat(a.debut), date.fromisoformat(a.jusqu_au)
    fin_ecl = date.fromisoformat(a.eclipses_jusqu_au) if a.eclipses_jusqu_au else fin
    jours, j = {}, debut
    while j <= fin:
        jours[j.isoformat()] = {str(h): [[n, r] for n, r in v] for h, v in occupation(j, c).items()}
        j += timedelta(days=1)
    res = {"systeme_maisons": systeme, "fuseau_naissance": tz, "decalage_naissance_utc": decalage,
           "lat": lat, "lon": lon, "cuspides": c, "jours": jours,
           "eclipses": [[d.isoformat(), t, m] for d, t, m in eclipses(debut, fin_ecl, c)]}
    with open(a.sortie, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
