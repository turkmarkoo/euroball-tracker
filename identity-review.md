# Team identities and image review — 8 September 2026

The directory now shows 261 teams instead of 352 cards. 70 groups of duplicate names account for 85 redundant cards. Six competition/status placeholders are excluded from the directory, while their stories remain searchable.

Aris, Aris Betsson and Aris Thessaloniki share one page with 14 stories. Besiktas and Beşiktaş share one page with 12 distinct stories. Other groups include Milan, Manresa, Girona, Krka, Budućnost, Cantù, Varese, Rotterdam and Spirou.

The visible story count changes from 1078 to 1074: four copies of the same dated event now combine after the club identity is normalized. The existing deduplication keeps source URLs and alternate IDs. Distinct dates, rumors, signings and extensions remain separate. Original downloaded transfer records and their source evidence remain intact.

## Behavior

- A shared explicit alias registry handles team cards, transfer rows, event deduplication and old team links.
- Searches include sponsor and historical names, even when a shorter display name is used.
- Similar but different teams remain distinct: AEK Athens/Larnaca, Aris Thessaloniki/Leeuwarden, Apollo Amsterdam/Apollon Patras, Krka/Krka youth, Ilirija/Lliria, and NBA/G League affiliates.
- No fuzzy matching runs in the application. Local edits are still applied before normalization.

## Sources reviewed

Club identities and imagery were compared against these public league and club sources. Each image has its exact originating URL and provider in [media.json](media.json).

- [Aris official site](https://arisbasketball.com/en/) and [Beşiktaş basketball](https://bjk.com.tr/en/takim/10/).
- [Euroleague Basketball club directory API](https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/clubs) and [EuroCup directory](https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/clubs); player headshots from 2022–2026 season rosters.
- [ABA League](https://www.aba-liga.com/) and its [Ilirija profile](https://www.aba-liga.com/team/92).
- [ACB Manresa profile](https://acb.com/es/liga/equipos/kidsandus-manresa-10), which includes the club's earlier BAXI name and current Kids&Us branding.
- [easyCredit BBL players and teams](https://www.easycredit-bbl.de/saison/unsere-spieler), [PLK teams](https://plk.pl/druzyny), [LKL teams](https://en.lkl.lt/komandos), [Greek league](https://www.esake.gr/), and [VTB League](https://vtb-league.com/en/).
- [Cantù sponsorship confirmation](https://www.legapallacanestro.com/acqua-sbernardo-e-pallacanestro-cant%C3%B9-insieme-altre-tre-stagioni), [Forlì official site](https://www.pallacanestroforli2015.it/) and [Astana](https://astanabasket.kz/).
- [Rotterdam official site](https://rcb.nl/), [Erokspor basketball](https://eroksporfk.com/basketbol), and [Romanian federation club register](https://www.frbaschet.ro/stiri/stiri/lista-structurilor-afiliate-definitiv-la-federatia-romana-de-baschet-0).
- [NBA teams](https://www.nba.com/teams) and [players](https://www.nba.com/players).
- [ScoutBasketball public player search](https://scoutbasketball.com/players) and [competitions](https://scoutbasketball.com/competitions), including BNXT, Italian, French, Turkish, Romanian, Hungarian and other domestic league club lists. This is ScoutBasketball, not a confirmed identification of the user's suggested EuroScout website.

## Image coverage and verification

239/261 team identities have sourced crests, up from 64 when the old media set is counted against the combined identities. Player portraits increase from 215 to 655. All 901 unique image URLs returned HTTP 200 during this review. The browser also loaded the reviewed Aris and Beşiktaş crests and sample player images successfully.

An exact-name search was performed for each of 630 initially missing player names. Nine searches with multiple portraits were skipped. Other missing images were unavailable under an exact match. The complete remaining list is in [media-review.json](media-review.json). No placeholder portraits or inferred photos based on a surname alone were added.

Images remain lazy-loaded. Failure falls back to initials. Image availability and current kit can change at the source.

## Combined team names

| Shared team | Previous separate cards |
| --- | --- |
| Promitheas Patras | Promitheas Patras; Promitheas |
| Yukatel Denizli | Yukatel Denizli; Merkezefendi |
| Siauliai | Siauliai; BC Siauliai |
| Kolossos Rhodes | Kolossos Rhodes; Kolossos Rodou |
| Krka | Krka; Krka Novo Mesto |
| Bosna BH Telecom | Bosna BH Telecom; Bosna |
| Široki TT Kabeli | Široki TT Kabeli; HKK Široki |
| Rotterdam City | Rotterdam City; Rotterdam City Basketball; ZZ Rotterdam |
| Bàsquet Girona | Bàsquet Girona; Girona; Basquet Girona; Basket Girona |
| DEAC Debrecen | DEAC Debrecen; DEAC |
| AEK Athens | AEK Athens; AEK |
| SCM Politehnica Timișoara | SCM Politehnica Timișoara; SCM Politehnica Timisoara; BC Timisoara |
| FC Argeș Pitești | FC Argeș Basketball; FC Argeș Pitești; FC Arges Pitesti; FC Arges Basketball |
| Avtodor Saratov | Avtodor Saratov; BC Avtodor Saratov |
| La Laguna Tenerife | La Laguna Tenerife; Tenerife |
| Dinamo București | Dinamo București; Dinamo Bucuresti |
| ZZ Leiden | ZZ Leiden; Zorg en Zekerheid Leiden |
| UBT Cluj-Napoca | UBT Cluj-Napoca; U-Banca Transilvania Cluj-Napoca |
| Nizhny Novgorod | Nizhny Novgorod; Pari Nizhny Novgorod |
| Neptunas Klaipeda | Neptunas Klaipeda; Neptunas |
| Boulazac Basket Dordogne | Boulazac; Boulazac Basket Dordogne |
| Río Breogán | Rio Breogan; Río Breogán |
| Enisey Krasnoyarsk | Enisey; Enisey Krasnoyarsk |
| Rytas Vilnius | Rytas; Rytas Vilnius |
| Buducnost VOLI | Buducnost VOLI; Budućnost VOLI |
| Galatasaray | Galatasaray MCT Technic; Galatasaray |
| Aris Thessaloniki | Aris Thessaloniki; Aris Betsson; Aris |
| FMP | FMP; FMP Meridian |
| Perspektiva Ilirija | Perspektiva Ilirija; KK Ilirija; Ilirija |
| Pallacanestro Varese | Openjobmetis Varese; Itelyum Varese; Pallacanestro Varese |
| Samara | Samara; BC Samara |
| Bamberg Baskets | Bamberg Baskets; BMA365 Bamberg |
| Windrose Giants Antwerp | Windrose Giants Antwerp; Giants Antwerp |
| Spartak Office Shoes | Spartak Subotica; Spartak Office Shoes |
| Juventus Utena | Juventus Utena; Utenos Juventus |
| CB Liège | CB Liège; CB Liege |
| Derthona Tortona | Derthona Tortona; Bertram Derthona |
| Bahcesehir Koleji | Bahcesehir; Bahcesehir Koleji |
| Napoli Basket | Napoli Basket; Napoli Basketball |
| Zalgiris Kaunas | Zalgiris Kaunas; Žalgiris Kaunas |
| Zenit St. Petersburg | Zenit St Petersburg; Zenit St. Petersburg |
| BAXI Manresa | Manresa; BAXI Manresa; Kids&Us Manresa |
| UNA Hotels Reggio Emilia | Reggio Emilia; UNA Hotels Reggio Emilia |
| Olimpia Milano | Olimpia Milano; EA7 Emporio Armani Milan; EA7 Olimpia Milano |
| Unicaja Malaga | Unicaja Malaga; Unicaja |
| Zadar | Zadar; KK Zadar |
| Esenler Erokspor | Safiport Erokspor; Esenler Erokspor |
| Pallacanestro Cantù | Cantu; Acqua S.Bernardo Cantù; Pallacanestro Cantù |
| Split | Split; KK Split |
| MBA Moscow | MBA Moscow; MBA; MBA-MAI |
| Parma | Parma; BETCITY PARMA |
| Beşiktaş | Besiktas; Beşiktaş |
| Lietkabelis | Lietkabelis; Lietkabelis Panevezys |
| Gran Canaria | Gran Canaria; Dreamland Gran Canaria |
| Turk Telekom | Turk Telekom; Türk Telekom |
| Karditsa | Karditsa; AS Karditsa |
| Le Mans Sarthe | Le Mans; Le Mans Sarthe |
| Spirou Charleroi | Val-Dieu Spirou Basket; Spirou Charleroi; Spirou Basket; Val-Dieu Spirou Charleroi |
| Germani Brescia | Germani Brescia; Pallacanestro Brescia |
| Czarni Słupsk | Energa Czarni Słupsk; Czarni Słupsk |
| CSM Galati | CSM Galati; CS Municipal Galati |
| Hamburg Towers | Hamburg Towers; Veolia Towers Hamburg |
| Gladiators Trier | Gladiators Trier; VET-CONCEPT Trier |
| Kangoeroes Mechelen | Kangoeroes Mechelen; Kangoeroes Basket Mechelen |
| Força Lleida | Hiopos Lleida; Força Lleida |
| Surne Bilbao Basket | Surne Bilbao Basket; Surne Bilbao |
| Leyma Coruña | Leyma Coruna; Leyma Coruña |
| RASTA Vechta | Rasta Vechta; RASTA Vechta |
| Szolnoki Olaj | Szolnoki Olaj; NHSZ-Szolnoki Olajbanyasz |
| Stal Ostrow Wielkopolski | Stal Ostrow Wielkopolski; Stal Ostrów Wlkp. |

## Validation

10 data regression tests cover aliases, sponsor searches, old links, distinct clubs, same-event source preservation, malformed inputs and image provenance. Desktop and 390px mobile checks confirm combined club pages and no horizontal overflow. Source credits are available from the Sources page and player details identify the photo provider.
