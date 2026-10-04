"""Nouvelles et pleines lunes d'une période.

Usage :
  python3 -m moteur.lunaisons --debut 2026-10-03 --fin 2027-01-02
  python3 -m moteur.lunaisons --prochaine

Affiche pour chaque lunaison : type, signe, date et heure de Paris, fenêtre de 3 jours avant et après.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

SIGNES = ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge", "Balance",
          "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"]
PARIS = ZoneInfo("Europe/Paris")


def _elong(j):
    return (swe.calc_ut(j, swe.MOON)[0][0] - swe.calc_ut(j, swe.SUN)[0][0]) % 360


def _instant(j0, cible):
    j = j0
    while True:
        d1 = (_elong(j) - cible + 180) % 360 - 180
        d2 = (_elong(j + .25) - cible + 180) % 360 - 180
        if d1 <= 0 < d2:
            a, b = j, j + .25
            for _ in range(40):
                m = (a + b) / 2
                if (_elong(m) - cible + 180) % 360 - 180 < 0:
                    a = m
                else:
                    b = m
            return (a + b) / 2
        j += .25


def lunaisons(debut, fin):
    res, j = [], swe.julday(debut.year, debut.month, debut.day, 0)
    while True:
        nl, pl = _instant(j, 0), _instant(j, 180)
        t = min(nl, pl)
        y, m, d, h = swe.revjul(t)
        u = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)
        if u.date() > fin:
            return res
        lon = swe.calc_ut(t, swe.MOON)[0][0]
        loc = u.astimezone(PARIS)
        res.append({
            "type": "Nouvelle lune" if t == nl else "Pleine lune",
            "signe": SIGNES[int(lon // 30)],
            "date": loc.date().isoformat(),
            "heure_paris": loc.strftime("%H h %M"),
            "fenetre": [(loc.date() - timedelta(days=3)).isoformat(), (loc.date() + timedelta(days=3)).isoformat()],
            "degre_interne": round(lon % 30, 2),
        })
        j = t + 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--debut")
    p.add_argument("--fin")
    p.add_argument("--prochaine", action="store_true")
    a = p.parse_args()
    if a.prochaine:
        today = date.today()
        print(json.dumps(lunaisons(today, today + timedelta(days=16))[:1], ensure_ascii=False, indent=1))
    else:
        print(json.dumps(lunaisons(date.fromisoformat(a.debut), date.fromisoformat(a.fin)), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
