"""The demo agents (also the templates a new agent can start from): three Montréal restaurant guides.

The guides and their experts are invented; the restaurants are real, described only with long-known, general facts
(no prices or opening hours). Every answer says to check before going. Edit freely: content can be swapped for any
subject (the studio doesn't care what the knowledge is about).

TEMPLATES[key] = {name, tagline_en/fr, domain, tone, expert(name, title, email), greeting_en/fr, scope_en/fr, refuse,
                  face, sources [(title, kind, body)], topics [(q_en, q_fr, a_en, a_fr, keywords, status, note)],
                  versions [(note, how many approved topics were in it)], gaps [question]}
"""

CHECK_EN = " Check opening hours before you go."
CHECK_FR = " Vérifiez les heures d'ouverture avant d'y aller."

TEMPLATES = {
    "classics": {
        "name": "Mireille",
        "tagline_en": "Your guide to Montréal's classic eats",
        "tagline_fr": "Votre guide des grands classiques de Montréal",
        "domain": "Montréal's classic restaurants",
        "tone": "warm",
        "expert": ("Hélène Gagnon", "Food writer, 20 years on the Montréal beat", "helene.demo@example.com"),
        "greeting_en": "Bonjour-hi! I'm Mireille. Ask me where to find Montréal's classics: smoked meat, bagels, poutine and the bistros locals love.",
        "greeting_fr": "Bonjour! Je suis Mireille. Demandez-moi où trouver les classiques de Montréal : smoked meat, bagels, poutine et les bistros chouchous des gens d'ici.",
        "scope_en": "The restaurants and foods Montréal is famous for. Institutions, markets and the dishes visitors ask about first.",
        "scope_fr": "Les restaurants et les plats qui ont fait la réputation de Montréal. Les institutions, les marchés et les plats que les visiteurs demandent en premier.",
        "refuse": ["allergy advice", "booking on your behalf"],
        "face": {"skin": "#EBB897", "hair": "#4A2E1F", "hairStyle": "bob", "eyes": "#3B2A20", "brows": "soft",
                 "glasses": "round", "accessory": "earrings", "shirt": "#B0007A", "bg": "#F8E3F0",
                 "voice": {"rate": 1, "pitch": 1.1}},
        "sources": [
            ("Hélène's classics notes", "notes",
             "Schwartz's on Saint-Laurent Boulevard has been slicing Montréal smoked meat since 1928. Regulars order "
             "it medium-fat, with fries, a pickle and a black cherry soda. Expect a line at lunch and on weekends. "
             "Fairmount Bagel opened in 1919 and St-Viateur Bagel in 1957, both in Mile End. Both hand-roll their "
             "bagels, boil them in honey water and bake them in a wood-fired oven. Sesame is the classic order. "
             "La Banquise, near Parc La Fontaine, is famous for late-night poutine with dozens of versions on the menu. "
             "A classic poutine is fries, squeaky fresh cheese curds and hot gravy. L'Express on Saint-Denis has been a "
             "Montréal institution since 1980, with its zinc bar, chalkboard specials and jars of cornichons on every "
             "table. Book ahead for dinner. Jean-Talon Market in Little Italy is one of the largest open-air markets in "
             "North America, with farmers, cheese shops and bakeries. Wilensky's Light Lunch on Fairmount Avenue has "
             "served its grilled salami and bologna Special with mustard since 1932."),
            ("Notes de classiques d'Hélène", "notes",
             "Schwartz's, sur le boulevard Saint-Laurent, tranche du smoked meat depuis 1928. Les habitués le prennent "
             "mi-gras, avec frites, cornichon et soda à la cerise noire. Prévoyez une file le midi et la fin de semaine. "
             "Fairmount Bagel a ouvert en 1919 et St-Viateur Bagel en 1957, tous deux dans le Mile End. Les deux roulent "
             "leurs bagels à la main, les pochent dans l'eau miellée et les cuisent au four à bois. Le sésame est le "
             "classique. La Banquise, près du parc La Fontaine, est célèbre pour sa poutine de fin de soirée et ses "
             "dizaines de variantes. Une poutine classique, ce sont des frites, du fromage en grains qui fait couic-couic "
             "et une sauce brune bien chaude. L'Express, rue Saint-Denis, est une institution depuis 1980, avec son bar "
             "en zinc, son ardoise et ses pots de cornichons sur chaque table. Réservez pour le souper. Le marché "
             "Jean-Talon, dans la Petite Italie, est l'un des plus grands marchés publics à ciel ouvert d'Amérique du "
             "Nord."),
        ],
        "topics": [
            ("Where do I get the best smoked meat?", "Où trouver le meilleur smoked meat?",
             "Schwartz's on Saint-Laurent Boulevard is the classic: it has been slicing Montréal smoked meat since 1928. Order it medium-fat with fries and a pickle, and expect a line at lunch." + CHECK_EN,
             "Schwartz's, sur le boulevard Saint-Laurent, est le classique : on y tranche du smoked meat depuis 1928. Prenez-le mi-gras, avec frites et cornichon, et prévoyez une file le midi." + CHECK_FR,
             "smoked meat viande fumee schwartz sandwich deli", "approved", ""),
            ("St-Viateur or Fairmount: which bagel is better?", "St-Viateur ou Fairmount : quel bagel est le meilleur?",
             "Both are in Mile End, both hand-roll their bagels, boil them in honey water and bake them in a wood-fired oven. Fairmount opened in 1919, St-Viateur in 1957. Get a warm sesame bagel from each and pick your side.",
             "Les deux sont dans le Mile End, roulent leurs bagels à la main, les pochent dans l'eau miellée et les cuisent au four à bois. Fairmount a ouvert en 1919, St-Viateur en 1957. Prenez un bagel sésame tout chaud chez chacun et choisissez votre camp.",
             "bagel bagels mile end sesame fairmount viateur", "approved", ""),
            ("Where should I try poutine?", "Où goûter une poutine?",
             "La Banquise, near Parc La Fontaine, is the famous choice, with dozens of versions on the menu. For your first one, keep it classic: fries, squeaky cheese curds and hot gravy.",
             "La Banquise, près du parc La Fontaine, est le choix célèbre, avec des dizaines de variantes au menu. Pour une première, restez classique : frites, fromage en grains qui fait couic-couic et sauce brune bien chaude.",
             "poutine fries frites curds fromage grains banquise gravy sauce", "approved", ""),
            ("I want a classic French bistro.", "Je cherche un bistro français classique.",
             "L'Express on Saint-Denis has been a Montréal institution since 1980: a long zinc bar, chalkboard specials and jars of cornichons on every table. Book ahead for dinner.",
             "L'Express, rue Saint-Denis, est une institution depuis 1980 : un long bar en zinc, une ardoise de plats du jour et des pots de cornichons sur chaque table. Réservez pour le souper.",
             "bistro french francais express saint denis", "approved", ""),
            ("Where can I shop for food like a local?", "Où faire son marché comme les gens d'ici?",
             "Head to Jean-Talon Market in Little Italy, one of the largest open-air markets in North America. Come hungry: farmers, cheese shops and bakeries line the aisles, and the stalls change with the seasons.",
             "Allez au marché Jean-Talon, dans la Petite Italie, l'un des plus grands marchés publics à ciel ouvert d'Amérique du Nord. Venez le ventre vide : producteurs, fromageries et boulangeries bordent les allées, au fil des saisons.",
             "market marche jean talon local produce groceries epicerie", "approved", ""),
            ("What is a Wilensky Special?", "C'est quoi, un Wilensky Special?",
             "It's the grilled salami and bologna sandwich with mustard served at Wilensky's Light Lunch on Fairmount Avenue since 1932. House rule: it always comes with mustard.",
             "C'est le sandwich grillé au salami et au bologne, avec moutarde, servi chez Wilensky's Light Lunch, avenue Fairmount, depuis 1932. Règle de la maison : toujours avec moutarde.",
             "wilensky special sandwich fairmount salami bologna", "approved", ""),
            ("Where do locals go for weekend brunch?", "Où les gens d'ici vont-ils bruncher la fin de semaine?",
             "", "", "brunch weekend fin semaine", "draft", ""),
            ("Is there a vegetarian smoked meat?", "Existe-t-il un smoked meat végétarien?",
             "Some delis and vegan spots in town now make a plant-based take on smoked meat. Ask at the counter what they have that day.",
             "Quelques delis et restos véganes proposent maintenant une version végétale du smoked meat. Demandez au comptoir ce qu'ils ont ce jour-là.",
             "vegetarian vegetarien vegan vegane smoked meat", "in_review", ""),
        ],
        "versions": [("First guide: smoked meat, bagels, poutine, bistro, market", 5),
                     ("Added the Wilensky Special", 6)],
        "gaps": ["Where can I get gluten-free bagels?", "Is Schwartz's open on Christmas Day?",
                 "Où acheter de la tire d'érable?"],
    },
    "nightbites": {
        "name": "Théo",
        "tagline_en": "Late-night and budget eats, no fuss",
        "tagline_fr": "Bouffe de nuit et petits budgets, sans chichis",
        "domain": "late-night and cheap eats in Montréal",
        "tone": "witty",
        "expert": ("Karim Haddad", "Line cook and night-shift regular", "karim.demo@example.com"),
        "greeting_en": "Hey, it's Théo. Hungry at 2 a.m. or down to your last twenty? I know where to go.",
        "greeting_fr": "Salut, c'est Théo. Une fringale à 2 h du matin ou plus que vingt piasses? Je sais où aller.",
        "scope_en": "Where to eat late at night and on a budget in Montréal.",
        "scope_fr": "Où manger tard le soir et sans se ruiner à Montréal.",
        "refuse": ["allergy advice", "anything illegal"],
        "face": {"skin": "#8D5A3B", "hair": "#1F1714", "hairStyle": "short", "eyes": "#2A2A2A", "brows": "straight",
                 "glasses": "none", "accessory": "none", "shirt": "#1B1A22", "bg": "#E1EFEC",
                 "voice": {"rate": 1.08, "pitch": 0.9}},
        "sources": [
            ("Karim's night list", "notes",
             "La Banquise is open around the clock and is the go-to after midnight. The Mile End bagel bakeries famously "
             "bake through the night, so a warm bag of bagels at 2 a.m. is a real Montréal move. Montréal's Chinatown, "
             "around De la Gauchetière Street, is the place for affordable dumplings and noodles. Walk the pedestrian "
             "strip and pick the busiest window. The Plateau has a strong Portuguese community, and charcoal-grilled "
             "chicken is its gift to the city. Romados on Rachel Street is a long-time favourite for chicken with fries "
             "and a custard tart. Bagels, a smoked meat sandwich, a quarter chicken or a bowl of dumplings all fill you up "
             "without breaking the bank."),
            ("La liste de nuit de Karim", "notes",
             "La Banquise est ouverte jour et nuit et c'est la valeur sûre après minuit. Les boulangeries de bagels du "
             "Mile End cuisent toute la nuit : un sac de bagels chauds à 2 h du matin, c'est très montréalais. Le "
             "quartier chinois, autour de la rue De La Gauchetière, est l'endroit pour des dumplings et des nouilles pas "
             "chers. Le Plateau a une grande communauté portugaise, et le poulet grillé au charbon est son cadeau à la "
             "ville. Romados, rue Rachel, est un favori de longue date pour le poulet, les frites et le pastel de nata."),
        ],
        "topics": [
            ("Where can I eat after midnight?", "Où manger après minuit?",
             "La Banquise is the go-to: it's open around the clock. The Mile End bagel bakeries also famously bake through the night, so a warm bag of bagels at 2 a.m. is a real Montréal move." + CHECK_EN,
             "La Banquise, c'est la valeur sûre : elle est ouverte jour et nuit. Les boulangeries de bagels du Mile End cuisent aussi toute la nuit : un sac de bagels chauds à 2 h du matin, c'est très montréalais." + CHECK_FR,
             "midnight late night apres minuit tard nuit open ouvert 24", "approved", ""),
            ("Where can I get cheap dumplings?", "Où trouver des dumplings pas chers?",
             "Chinatown, around De la Gauchetière Street, is your place for affordable dumplings and noodles. Walk the pedestrian strip and pick the busiest window: busy means fresh.",
             "Le quartier chinois, autour de la rue De La Gauchetière, est l'endroit pour des dumplings et des nouilles pas chers. Marchez dans la rue piétonne et choisissez la vitrine la plus achalandée : achalandé veut dire frais.",
             "dumplings raviolis chinatown quartier chinois cheap noodles nouilles", "approved", ""),
            ("Where do I find Portuguese chicken?", "Où manger du poulet portugais?",
             "Head to the Plateau: charcoal-grilled Portuguese chicken is its gift to the city. Romados on Rachel Street is a long-time favourite. Get the chicken with fries and finish with a custard tart.",
             "Direction le Plateau : le poulet portugais grillé au charbon est son cadeau à la ville. Romados, rue Rachel, est un favori de longue date. Prenez le poulet avec frites et finissez avec un pastel de nata.",
             "portuguese portugais chicken poulet romados rachel plateau grill", "approved", ""),
            ("What's good to eat on a small budget?", "Quoi manger avec un petit budget?",
             "Bagels, a smoked meat sandwich, a quarter chicken or a bowl of dumplings will all fill you up without breaking the bank. Prices change, so take this as a direction, not a quote.",
             "Des bagels, un sandwich au smoked meat, un quart de poulet ou un bol de dumplings vous rempliront sans vous ruiner. Les prix changent : c'est une piste, pas une soumission.",
             "cheap budget pas cher petit budget money argent affordable", "approved", ""),
            ("Where's the best late-night ramen?", "Où manger des ramen tard le soir?",
             "There are a few ramen bars downtown that stay open late on weekends.", "",
             "ramen late night soir noodles", "changes", "Name a place we've actually checked, please, and add the French."),
        ],
        "versions": [("Night list, first edition", 4)],
        "gaps": ["Late-night tacos?", "Any 24-hour diners in Verdun?"],
    },
    "specialnight": {
        "name": "Margaux",
        "tagline_en": "Where to book for a special night out",
        "tagline_fr": "Où réserver pour une soirée spéciale",
        "domain": "special-occasion dining in Montréal",
        "tone": "calm",
        "expert": ("Sophie Tremblay", "Sommelier", "sophie.demo@example.com"),
        "greeting_en": "Good evening, I'm Margaux. Celebrating something? Let's find you the right table.",
        "greeting_fr": "Bonsoir, je suis Margaux. Vous célébrez quelque chose? Trouvons-vous la bonne table.",
        "scope_en": "Restaurants for dates, anniversaries and big occasions in Montréal.",
        "scope_fr": "Des restaurants pour les rendez-vous, les anniversaires et les grandes occasions à Montréal.",
        "refuse": ["allergy advice", "booking on your behalf"],
        "face": {"skin": "#F6D7C3", "hair": "#B4473A", "hairStyle": "wavy", "eyes": "#4C6A3A", "brows": "arched",
                 "glasses": "none", "accessory": "scarf", "shirt": "#3E5A99", "bg": "#E9E4F2",
                 "voice": {"rate": 0.95, "pitch": 1}},
        "sources": [
            ("Sophie's special-occasion notes", "notes",
             "Joe Beef in Little Burgundy is the name everyone mentions for a big night: generous, rich, very Montréal. "
             "Its sister restaurant Liverpool House, a few doors down Notre-Dame Street West, can be easier to book. "
             "Au Pied de Cochon, chef Martin Picard's restaurant on the Plateau, is famous for indulgent Québécois "
             "cooking, including its foie gras poutine. Toqué!, led by chef Normand Laprise, is one of the city's "
             "long-standing fine-dining tables, known for Québec ingredients and tasting menus. Olive et Gourmando in "
             "Old Montréal is a bakery-café loved for its sandwiches, pastries and weekend crowds."),
            ("Notes de Sophie pour les grandes occasions", "notes",
             "Joe Beef, dans la Petite-Bourgogne, est le nom que tout le monde cite pour une grande soirée : généreux, "
             "riche, très montréalais. Son petit frère Liverpool House, quelques portes plus loin rue Notre-Dame Ouest, "
             "est parfois plus facile à réserver. Au Pied de Cochon, le restaurant du chef Martin Picard sur le Plateau, "
             "est célèbre pour sa cuisine québécoise généreuse, dont sa poutine au foie gras. Toqué!, du chef Normand "
             "Laprise, est une grande table de longue date, connue pour ses produits du Québec et ses menus dégustation."),
        ],
        "topics": [
            ("Where should I go for a special dinner?", "Où aller pour un souper spécial?",
             "Joe Beef in Little Burgundy is the name everyone mentions: generous, rich, very Montréal. Its sister restaurant Liverpool House, a few doors down Notre-Dame Street West, can be easier to book.",
             "Joe Beef, dans la Petite-Bourgogne, est le nom que tout le monde cite : généreux, riche, très montréalais. Son petit frère Liverpool House, quelques portes plus loin rue Notre-Dame Ouest, est parfois plus facile à réserver.",
             "special dinner souper date anniversary anniversaire joe beef liverpool", "approved", ""),
            ("Tell me about Au Pied de Cochon.", "Parlez-moi d'Au Pied de Cochon.",
             "Au Pied de Cochon is chef Martin Picard's restaurant on the Plateau, famous for indulgent Québécois cooking, including its foie gras poutine. Go hungry and share.",
             "Au Pied de Cochon est le restaurant du chef Martin Picard sur le Plateau, célèbre pour sa cuisine québécoise généreuse, dont sa poutine au foie gras. Venez affamé et partagez.",
             "pied cochon picard foie gras quebecois plateau", "approved", ""),
            ("Where can I have a tasting menu?", "Où prendre un menu dégustation?",
             "Toqué!, led by chef Normand Laprise, is one of the city's long-standing fine-dining tables, known for Québec ingredients. It's the choice for a tasting menu and a big occasion.",
             "Toqué!, du chef Normand Laprise, est une grande table de longue date, connue pour ses produits du Québec. C'est le choix pour un menu dégustation et une grande occasion.",
             "tasting menu degustation fine dining gastronomique toque laprise", "approved", ""),
            ("Where can we have brunch in Old Montréal?", "Où bruncher dans le Vieux-Montréal?",
             "Olive et Gourmando in Old Montréal is a bakery-café loved for its sandwiches, pastries and weekend crowds. Go early or be ready to wait.",
             "Olive et Gourmando, dans le Vieux-Montréal, est un café-boulangerie adoré pour ses sandwichs, ses viennoiseries et ses foules de fin de semaine. Allez-y tôt ou soyez prêt à attendre.",
             "brunch old montreal vieux olive gourmando cafe pastries viennoiseries", "approved", ""),
        ],
        "versions": [("Opening list for special nights", 4)],
        "gaps": ["Restaurant with a view for a proposal?"],
    },
}
ORDER = ["classics", "nightbites", "specialnight"]


def template(key):
    return TEMPLATES.get(key)


def template_list():
    return [{"key": k, "name": TEMPLATES[k]["name"], "tagline": TEMPLATES[k]["tagline_en"],
             "face": TEMPLATES[k]["face"], "topics": len(TEMPLATES[k]["topics"]), "sources": len(TEMPLATES[k]["sources"])}
            for k in ORDER]
