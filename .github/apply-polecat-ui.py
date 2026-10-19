#!/usr/bin/env python3
# Applies the Polecat UI customisations to the Falkon sources at build time.
#
#   * adds the New Tab "hero": live clock, greeting with the system user name,
#     and a search box, injected into Falkon's Speed Dial page.
#
# The wallpaper itself is committed as real files
# (src/lib/data/html/sd_light_bg.svg and sd_dark_bg.svg).
#
# The script is idempotent and fails loudly if an anchor is missing.
import sys

PATH = "src/lib/network/schemehandlers/falkonschemehandler.cpp"

src = open(PATH, encoding="utf-8").read()

if "POLECATHERO" in src:
    print("Polecat UI already applied, nothing to do")
    sys.exit(0)

if "#include <QJsonArray>" not in src:
    anchor = "#include <QTimer>"
    if anchor not in src:
        sys.exit("ERROR: include anchor not found in " + PATH)
    src = src.replace(anchor, "#include <QDir>\n#include <QJsonArray>\n#include <QJsonDocument>\n#include <QTimer>", 1)

old = '    page.replace(QLatin1String("%INITIAL-SCRIPT%"), QString::fromLatin1(dial->initialScript().toUtf8().toBase64()));'
if old not in src:
    sys.exit("ERROR: speeddialPage anchor not found in " + PATH)

HERO = '''    // ---- Polecat new tab hero: clock, greeting and search ----------------
    // Injected here so the customisation needs no extra source files. The user
    // name is embedded as a JSON string literal, so it cannot break markup.
    {
        QString user = qEnvironmentVariable("USER");
        if (user.isEmpty()) {
            user = QDir::home().dirName();
        }

        static const char *const kHero = R"POLECATHERO(
<style>
#sd-hero{text-align:center;margin:26px auto 8px;max-width:720px;padding:0 16px}
#sd-clock{font-size:clamp(46px,8vw,84px);font-weight:700;letter-spacing:-2px;line-height:1;color:#fff;text-shadow:0 2px 20px rgba(0,0,0,.45)}
#sd-date{font-size:13px;color:#fff;opacity:.92;margin-top:5px;text-shadow:0 1px 10px rgba(0,0,0,.55)}
#sd-welcome{font-size:15px;color:#fff;margin:14px 0;text-shadow:0 1px 10px rgba(0,0,0,.55)}
#sd-search{width:100%;box-sizing:border-box;height:50px;padding:0 22px;border-radius:25px;border:1px solid rgba(255,255,255,.65);background:rgba(255,255,255,.9);color:#202124;font-size:15px;outline:none;box-shadow:0 6px 22px rgba(0,0,0,.22)}
#sd-search:focus{background:#fff}
@media (prefers-color-scheme:dark){#sd-search{background:rgba(28,34,44,.82);color:#eaeaea;border-color:rgba(255,255,255,.16)}}
</style>
<div id="sd-hero">
  <div id="sd-clock">--:--</div>
  <div id="sd-date"></div>
  <div id="sd-welcome"></div>
  <form id="sd-searchform" autocomplete="off">
    <input id="sd-search" type="text" placeholder="Search anything with Polecat Browser&#8230;   Type Here">
  </form>
</div>
<script>
(function () {
  var USER = %POLECAT_USER_JSON%;
  var hero = document.getElementById('sd-hero');
  var dials = document.getElementById('quickdial');
  if (hero && dials && dials.parentNode) { dials.parentNode.insertBefore(hero, dials); }
  document.getElementById('sd-welcome').textContent = USER ? ('Welcome, ' + USER) : 'Welcome';
  document.documentElement.style.backgroundSize = 'cover';
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function tick() {
    var d = new Date();
    document.getElementById('sd-clock').textContent = pad(d.getHours()) + ':' + pad(d.getMinutes());
    var e = document.getElementById('sd-date');
    try { e.textContent = d.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }
    catch (x) { e.textContent = d.toDateString(); }
  }
  tick();
  setInterval(tick, 1000);
  document.getElementById('sd-searchform').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var v = document.getElementById('sd-search').value.trim();
    if (!v) { return; }
    var isUrl = /^(https?:\\/\\/|about:|file:|ftp:)/i.test(v) || (/^[^\\s]+\\.[^\\s]{2,}/.test(v) && v.indexOf(' ') === -1);
    location.href = isUrl ? (/^[a-z]+:/i.test(v) ? v : ('https://' + v)) : ('https://duckduckgo.com/?q=' + encodeURIComponent(v));
  });
})();
</script>
)POLECATHERO";

        QJsonArray userArray;
        userArray.append(user);
        QString userJson = QString::fromUtf8(QJsonDocument(userArray).toJson(QJsonDocument::Compact));
        userJson = userJson.mid(1, userJson.length() - 2); // strip the surrounding [ ]

        QString hero = QString::fromUtf8(kHero);
        hero.replace(QLatin1String("%POLECAT_USER_JSON%"), userJson);
        page.replace(QLatin1String("</body>"), hero + QLatin1String("</body>"));
    }

'''

src = src.replace(old, HERO + old, 1)
open(PATH, "w", encoding="utf-8").write(src)
print("Applied Polecat UI to " + PATH)
