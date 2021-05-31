"""Seed data definitions (fictional demo content)."""

ADMINS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Aarav Mehta",
        "password": "Admin@123",
        "is_verified": True,
    }
]

CUSTOMERS = [
    {"email": "priya@example.com", "username": "priya.sharma", "full_name": "Priya Sharma", "password": "Customer@123", "is_verified": True, "phone": "+91 9820011223"},
    {"email": "rohan@example.com", "username": "rohan.verma", "full_name": "Rohan Verma", "password": "Customer@123", "is_verified": True, "phone": "+91 9820044556"},
    {"email": "sara@example.com", "username": "sara.khan", "full_name": "Sara Khan", "password": "Customer@123", "is_verified": True, "phone": "+91 9820077889"},
    {"email": "dev@example.com", "username": "dev.patel", "full_name": "Dev Patel", "password": "Customer@123", "is_verified": False, "phone": "+91 9820099000"},
    {"email": "meera@example.com", "username": "meera.iyer", "full_name": "Meera Iyer", "password": "Customer@123", "is_verified": True, "phone": "+91 9812345678"},
]

ADDRESSES = [
    ("priya.sharma", "Home", "12 Marine Drive Apartments, Netaji Subhash Road", "Mumbai", "Maharashtra", "400020", True),
    ("priya.sharma", "Office", "4th Floor, Prism Tower, BKC", "Mumbai", "Maharashtra", "400051", False),
    ("rohan.verma", "Home", "C-42 SBI Colony, Opposite City Mall", "Varanasi", "Uttar Pradesh", "221002", True),
    ("sara.khan", "Home", "5-B Lake View Residency, Indiranagar", "Bengaluru", "Karnataka", "560038", True),
    ("dev.patel", "Home", "7 Rosewood Society, SG Highway", "Ahmedabad", "Gujarat", "380054", True),
    ("meera.iyer", "Home", "21 Anna Nagar Main Road", "Chennai", "Tamil Nadu", "600040", True),
]

CATEGORIES = [
    ("Fiction", "Imaginative prose across literary and popular traditions"),
    ("Mystery & Thriller", "Whodunnits, suspense and psychological thrillers"),
    ("Science Fiction & Fantasy", "Speculative worlds and epic imagination"),
    ("Mythology", "Ancient tales retold for modern readers"),
    ("Self-Help & Productivity", "Practical guides for work and life"),
    ("History", "Narratives from the past, examined closely"),
    ("Science", "Popular science and the natural world"),
    ("Biography & Memoir", "Lives worth reading about"),
    ("Poetry", "Verse collections across eras and voices"),
]

AUTHORS = [
    ("Jhumpa Lahiri", "Pulitzer-winning author known for quiet, precise portraits of Indian diaspora life."),
    ("Neil Gaiman", "Author of modern fantasy classics including American Gods and Coraline."),
    ("Dave Eggers", "American writer and publisher, founder of McSweeney's."),
    ("Michael Chabon", "Pulitzer-winning novelist celebrated for his maximalist prose."),
    ("Patti Smith", "Singer-songwriter and National Book Award-winning memoirist."),
    ("Raymond Carver", "Master of the American short story and minimalism."),
    ("Don DeLillo", "Postmodern novelist chronicling American anxiety."),
    ("John Steinbeck", "Nobel laureate and chronicler of Depression-era California."),
    ("George Saunders", "MacArthur fellow known for satirical, tender fiction."),
    ("Andy Weir", "Science-fiction writer of The Martian fame."),
    ("Agatha Christie", "The best-selling novelist of all time, creator of Poirot."),
    ("James Clear", "Writer and speaker focused on habits and continuous improvement."),
    ("Yuval Noah Harari", "Historian and author of the bestselling Sapiens trilogy."),
    ("S. Chandrasekhar", "Physicist and author of popular-science histories."),
    ("David Foster Wallace", "Essayist and novelist famed for his footnotes and ferocious intelligence."),
    ("Stieg Larsson", "Swedish journalist whose Millennium trilogy became a global phenomenon."),
    ("Gillian Flynn", "Author of dark, twist-laden thrillers including Gone Girl."),
    ("Alex Michaelides", "Screenwriter turned novelist with a taste for psychological puzzles."),
    ("Tara Westover", "Memoirist who wrote about growing up off the grid and finding education."),
    ("Michelle Obama", "Attorney, author and former First Lady of the United States."),
    ("Matt Haig", "British novelist writing hopeful, humane fiction about second chances."),
    ("Kazuo Ishiguro", "Nobel laureate known for restrained, devastating first-person fiction."),
    ("Frank Herbert", "Creator of the Dune universe and ecological science fiction."),
    ("J. R. R. Tolkien", "Philologist who more or less invented modern fantasy."),
    ("Sally Rooney", "Irish novelist of millennial intimacy and class."),
    ("Delia Owens", "Wildlife scientist turned bestselling novelist."),
    ("Marcus Aurelius", "Roman emperor and Stoic philosopher."),
    ("Daniel Kahneman", "Nobel-winning psychologist of judgment and decision-making."),
    ("Héctor García", "Japanese-based Spanish author writing on longevity and wellbeing."),
    ("Francesc Miralles", "Spanish author of self-help and fiction, co-writer of Ikigai."),
]

PUBLISHERS = [
    "HarperCollins", "Bloomsbury Publishing", "Penguin Books", "Vintage Classics",
    "Random House", "Ecco Press", "Picador", "Simon & Schuster", "Oxford Press",
]

# (title, [authors], categories, publisher, year, pages, price, discount, stock, featured, isbn, description)
BOOKS = [
    ("The Namesake", ["Jhumpa Lahiri"], ["Fiction"], "HarperCollins", 2007, 304, 299, 0, 32, True, "9780006551415", "A boy grows up negotiating the distance between his Bengali parents and his American world, bound by a name that carries his family's whole history."),
    ("Norse Mythology", ["Neil Gaiman"], ["Mythology", "Fiction"], "Bloomsbury Publishing", 2019, 304, 341, 10, 43, True, "9780393356182", "Gaiman retells the great Norse epics — from Odin's search for wisdom to Ragnarök — with wit, gravity and page-turning pace."),
    ("American Gods", ["Neil Gaiman"], ["Science Fiction & Fantasy", "Fiction"], "Random House", 2002, 736, 364, 15, 12, True, "9780062312863", "An ex-convict becomes entangled in a war between the old gods of immigration and the new gods of technology."),
    ("Interpreter of Maladies", ["Jhumpa Lahiri"], ["Fiction"], "HarperCollins", 2005, 198, 259, 0, 97, False, "9780006561971", "Eleven luminous stories map the terrains of love, loss and displacement between India and America."),
    ("The Circle", ["Dave Eggers"], ["Fiction"], "Penguin Books", 2014, 504, 395, 5, 26, False, "9780241956169", "A young woman joins the world's most powerful internet company and slowly discovers the cost of total transparency."),
    ("The Amazing Adventures of Kavalier & Clay", ["Michael Chabon"], ["Fiction"], "Random House", 2012, 701, 499, 0, 68, True, "9780812967164", "Two cousins invent golden-age comic-book heroes in 1940s New York in this Pulitzer-winning epic."),
    ("Just Kids", ["Patti Smith"], ["Biography & Memoir"], "Ecco Press", 2010, 304, 259, 0, 55, False, "9780060936228", "Patti Smith's National Book Award-winning memoir of her life and friendship with Robert Mapplethorpe."),
    ("A Heartbreaking Work of Staggering Genius", ["Dave Eggers"], ["Biography & Memoir"], "Picador", 2007, 437, 431, 0, 104, False, "9780330418922", "A memoir of grief and chaotic love: a young man raises his brother after their parents' deaths."),
    ("Coraline", ["Neil Gaiman"], ["Science Fiction & Fantasy"], "Bloomsbury Publishing", 2016, 208, 216, 20, 100, True, "9780747581051", "Coraline steps through a bricked-up doorway into a mirrored world that is wonderful, and wrong."),
    ("Where I'm Calling From", ["Raymond Carver"], ["Fiction", "Poetry"], "Vintage Classics", 1989, 526, 487, 0, 12, False, "9780679722388", "Thirty-seven stories that distill American working-class life to its clean, devastating essence."),
    ("White Noise", ["Don DeLillo"], ["Fiction"], "Penguin Books", 2017, 320, 699, 25, 49, False, "9780241370415", "A professor of Hitler studies faces an airborne toxic event in DeLillo's satire of consumer fear."),
    ("Cannery Row", ["John Steinbeck"], ["Fiction", "History"], "Penguin Books", 2011, 181, 434, 0, 95, False, "9780140187373", "A loving portrait of the misfits and dreamers of a sardine-canning street in Monterey."),
    ("Lincoln in the Bardo", ["George Saunders"], ["Fiction"], "Random House", 2017, 367, 100, 0, 250, True, "9780525511334", "In a graveyard between life and death, Abraham Lincoln grieves his young son in this experimental masterpiece."),
    ("Consider the Lobster", ["David Foster Wallace"], ["Fiction"], "Picador", 2007, 343, 582, 0, 92, False, "9780316156119", "Essays ranging from the Maine Lobster Festival to the meaning of honesty in journalism."),
    ("Project Hail Mary", ["Andy Weir"], ["Science Fiction & Fantasy"], "Random House", 2021, 476, 459, 10, 130, True, "9780593135204", "A lone astronaut must save humanity — and first he must solve a puzzle involving an alien vessel and a lot of physics."),
    ("The Martian", ["Andy Weir"], ["Science Fiction & Fantasy"], "Random House", 2014, 387, 399, 0, 88, False, "9780553418026", "Stranded on Mars with dwindling supplies, astronaut Mark Watney refuses to die quietly."),
    ("Murder on the Orient Express", ["Agatha Christie"], ["Mystery & Thriller"], "HarperCollins", 2017, 256, 299, 0, 76, True, "9780062693665", "A snowbound train, a locked compartment and twelve suspects: Hercule Poirot's most elegant case."),
    ("And Then There Were None", ["Agatha Christie"], ["Mystery & Thriller"], "HarperCollins", 2004, 272, 250, 5, 61, False, "9780062073481", "Ten strangers are lured to an island and eliminated one by one in Christie's darkest masterpiece."),
    ("Atomic Habits", ["James Clear"], ["Self-Help & Productivity"], "Penguin Books", 2018, 320, 599, 30, 210, True, "9780735211292", "A framework for building good habits and breaking bad ones, one tiny change at a time."),
    ("Sapiens: A Brief History of Humankind", ["Yuval Noah Harari"], ["History"], "Simon & Schuster", 2015, 443, 499, 20, 180, True, "9780062316097", "From foraging bands to data empires: a sweeping account of how Homo sapiens came to rule the planet."),
    ("Homo Deus: A Brief History of Tomorrow", ["Yuval Noah Harari"], ["History"], "Simon & Schuster", 2017, 464, 499, 0, 64, False, "9780062464316", "What happens to society when data outperforms intuition? Harari speculates about our algorithmic future."),
    ("Deep Work", ["James Clear"], ["Self-Help & Productivity"], "Penguin Books", 2016, 304, 449, 10, 5, False, "9781455586691", "Rules for focused success in a distracted world — why depth beats busyness."),
    ("The Cosmos: A Very Short Introduction", ["S. Chandrasekhar"], ["History", "Science"], "Oxford Press", 2019, 152, 199, 0, 30, False, "9780198820962", "An accessible tour of cosmic origins, from the Big Bang to black holes."),
    ("Lowland", ["Jhumpa Lahiri"], ["Fiction"], "Penguin Books", 2013, 340, 350, 0, 40, False, "9780307265738", "Two brothers bound by politics and love on the Bengal delta, across decades and continents."),
    ("Stardust", ["Neil Gaiman"], ["Science Fiction & Fantasy"], "Random House", 1999, 298, 299, 0, 58, False, "9780380804559", "A young man crosses the wall into Faerie to retrieve a fallen star that is not at all what he expects."),
    ("What We Talk About When We Talk About Love", ["Raymond Carver"], ["Fiction"], "Vintage Classics", 2003, 176, 301, 0, 23, False, "9780099530369", "Carver's couples argue, drink and confess in stories carved down to the bone."),
    ("The Girl with the Dragon Tattoo", ["Stieg Larsson"], ["Mystery & Thriller"], "Random House", 2008, 644, 399, 15, 70, True, "9780307454546", "A disgraced journalist and a hacker investigate a decades-old disappearance in icy Sweden."),
    ("Gone Girl", ["Gillian Flynn"], ["Mystery & Thriller"], "Random House", 2014, 419, 350, 0, 82, False, "9780307588370", "A wife disappears on her fifth anniversary and the husband becomes the prime suspect in a twisting media circus."),
    ("The Silent Patient", ["Alex Michaelides"], ["Mystery & Thriller"], "Penguin Books", 2019, 336, 299, 10, 96, True, "9781250301697", "A famous painter shoots her husband and never speaks again — until a psychotherapist becomes obsessed."),
    ("Educated", ["Tara Westover"], ["Biography & Memoir"], "Random House", 2018, 334, 399, 0, 74, False, "9780399590504", "A survivalist family, a thirst for learning, and the distance between a girl and her origins."),
    ("Becoming", ["Michelle Obama"], ["Biography & Memoir"], "Penguin Books", 2018, 426, 499, 15, 110, True, "9781524763138", "The former First Lady's intimate, powerful memoir of a life of meaning."),
    ("The Midnight Library", ["Matt Haig"], ["Fiction"], "Penguin Books", 2020, 288, 399, 0, 120, False, "9780525559474", "Between life and death lies a library where every book is a life you could have lived."),
    ("Klara and the Sun", ["Kazuo Ishiguro"], ["Science Fiction & Fantasy", "Fiction"], "Penguin Books", 2021, 303, 350, 0, 66, False, "9780593318171", "An artificial friend observes the human world with heartbreaking precision in this Nobel laureate's novel."),
    ("Dune", ["Frank Herbert"], ["Science Fiction & Fantasy"], "Random House", 2020, 658, 499, 20, 90, True, "9780441172719", "On desert Arrakis, Paul Atreides faces prophecy, spice and empire in science fiction's grandest saga."),
    ("The Hobbit", ["J. R. R. Tolkien"], ["Science Fiction & Fantasy"], "HarperCollins", 2012, 310, 349, 0, 140, False, "9780345339683", "Bilbo Baggins is swept into a quest of dwarves, dragons and one very precious ring."),
    ("Normal People", ["Sally Rooney"], ["Fiction"], "Penguin Books", 2019, 273, 299, 0, 84, False, "9781984822178", "Connell and Marianne circle each other through school and university in a tender study of class and intimacy."),
    ("Where the Crawdads Sing", ["Delia Owens"], ["Fiction", "Mystery & Thriller"], "Penguin Books", 2019, 384, 349, 10, 2, True, "9780735219090", "A marsh girl, an isolated coastline and a murder that forces the town to see her at last."),
    ("Meditations", ["Marcus Aurelius"], ["Self-Help & Productivity"], "Penguin Books", 2015, 254, 250, 0, 48, False, "9780140449334", "The private reflections of a Roman emperor on duty, mortality and the discipline of the mind."),
    ("Thinking, Fast and Slow", ["Daniel Kahneman"], ["Self-Help & Productivity"], "Penguin Books", 2012, 499, 550, 25, 6, False, "9780141033570", "A Nobel winner maps the two systems that drive the way we think — and the errors they produce."),
    ("Ikigai: The Japanese Secret to a Long and Happy Life", ["Héctor García", "Francesc Miralles"], ["Self-Help & Productivity"], "Penguin Books", 2017, 208, 299, 0, 58, False, "9780143130727", "Lessons from the longevity village of Ogimi on purpose, community and daily joy."),
]

COUPONS = [
    {"code": "WELCOME10", "description": "10% off your first order (min ₹500)", "discount_type": "percent", "value": 10, "min_order_amount": 500, "max_discount_amount": 200, "usage_limit": None},
    {"code": "BOOKLOVER25", "description": "Flat ₹25 off orders above ₹300", "discount_type": "fixed", "value": 25, "min_order_amount": 300, "max_discount_amount": None, "usage_limit": 500},
    {"code": "BIGSHELF15", "description": "15% off orders above ₹1500", "discount_type": "percent", "value": 15, "min_order_amount": 1500, "max_discount_amount": 400, "usage_limit": 200},
]

REVIEW_SNIPPETS = [
    ("A quiet marvel", "Picked this up on a rainy weekend and could not put it down. The prose is restrained but every sentence lands."),
    ("Exactly as described", "Beautiful edition, crisp printing and quick delivery. The story itself is a slow burn worth the patience."),
    ("Highly recommend", "I have already gifted two copies. Some chapters I re-read immediately just to savour the phrasing."),
    ("Good but demanding", "Requires your full attention, but rewards it richly. Not a casual read — a proper one."),
    ("Instant favourite", "Went in expecting one book and got something stranger and better. The ending stayed with me for days."),
    ("Solid storytelling", "Strong characters and a propulsive middle. A couple of slow patches, but the whole is greater."),
    ("Arrived in perfect condition", "Reviewing the purchase experience as much as the book: great packaging, genuine copy, fair price."),
    ("A modern classic", "It earns the label. Thematically rich without being showy about it."),
]
