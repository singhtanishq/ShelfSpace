DROP DATABASE IF EXISTS book_shop;
CREATE DATABASE book_shop;
USE book_shop;

-- --------------------------------------------Books Table -----------------------------------------------------------
 
CREATE TABLE books 
	(
		book_id INT PRIMARY KEY AUTO_INCREMENT,
		title VARCHAR(100) NOT NULL,
		author_fname VARCHAR(100) NOT NULL,
		author_lname VARCHAR(100) NOT NULL,
		released_year INT NOT NULL,
        category VARCHAR(40) NOT NULL,
        publication VARCHAR(100) NOT NULL,
		stock_quantity INT NOT NULL,
		pages INT NOT NULL,
        pg_word INT,
        price INT NOT NULL
	);

-- --------------------------------------------------------------------------------------------------------------------

INSERT INTO books (title, author_fname, author_lname, released_year, stock_quantity, pages, price, pg_word, publication, category)
VALUES
('the namesake', 'jhumpa', 'lahiri', 2007, 32, 304, 299, 150, 'Harpercollins (5 March 2007)', 'Classic'),
('norse mythology', 'neil', 'gaiman',2019, 43, 304, 341, 200, 'Bloomsbury Publishing (18 December 2019)', 'Mythology'),
('american gods', 'neil', 'gaiman', 2002, 12, 736, 364, 145, 'Headline Review (4 March 2002)', 'Drama'),
('interpreter of maladies', 'jhumpa', 'lahiri', 2005, 97, 198, 259, 125, 'Harpercollins Publishers India (5 September 2005)', 'Fantasy'),
('a hologram for the king: a novel', 'dave', 'eggers', 2013, 25, 154, 315, 129, 'Penguin UK (1 August 2013)', 'Travel'),
('the circle', 'dave', 'eggers', 2014, 26, 504, 395, 140, 'Penguin (24 April 2014)', 'Horror'),
('the amazing adventures of kavalier & clay', 'michael', 'chabon', 2012, 68, 701, 499, 165, 'Random House Trade Paperbacks (12 June 2012)', 'Adventure'),
('just kids', 'patti', 'smith', 2010, 55, 304, 259, 250, 'Ecco (2 November 2010)', 'Fairy Tale'),
('a heartbreaking work of staggering genius', 'dave', 'eggers', 2007, 104, 437, 431, 160, 'Picador (21 September 2007)', 'Humour'),
('coraline', 'neil', 'gaiman', 2016, 100, 208, 216, 175, "Bloomsbury Children's Books (30 August 2016)'", 'Mystery'),
('what we talk about when we talk about love: stories', 'raymond', 'carver', 2003, 23, 176, 301, 190, 'Vintage Classics (5 November 2009)', 'Love Story'),
("where i'm calling from: selected stories", 'raymond', 'carver', 1989, 12, 526, 487, 200, 'Vintage (18 June 1989)', 'Thriller'),
('white noise', 'don', 'delillo', 2017, 49, 320, 699, 180, 'Penguin Classics (18 January 2017)', 'Thriller'),
('cannery row', 'john', 'steinbeck', 2011, 95, 181, 434, 300, 'Penguin UK (16 May 2011)', 'Short Story'),
('oblivion: stories', 'david', 'foster wallace', 2005, 172, 329, 299, 200, 'Abacus (28 April 2005)', 'Suspense'),
('consider the lobster', 'david', 'foster wallace', 2007, 92, 343, 582, 230, 'Abacus (21 June 2007)', 'Collection of Essays'),
('10% happier', 'dan', 'harris', 2017, 29, 256, 485, 140, 'Yellow Kite (26 January 2017)', 'Romance'),
('lincoln in the bardo', 'george', 'saunders', 2017, 1000, 367, 100, 250, 'Bloomsbury Publishing (1 January 2017)', 'Drama');

ALTER TABLE books engine = InnoDB;

-- ---------------------------------------------Orders Table ------------------------------------------------------------
CREATE TABLE orders
	(ord_no INT PRIMARY KEY auto_increment,    -- 0
     customer_name VARCHAR(40) NOT NULL,       -- 1
     address VARCHAR(100) NOT NULL,            -- 2
	 district VARCHAR(30) NOT NULL,            -- 3
     city VARCHAR(30) NOT NULL,                -- 4
     state_ut VARCHAR(20) NOT NULL,            -- 5
     pincode INT NOT NULL,                     -- 6
     country VARCHAR(25) NOT NULL DEFAULT 'India', -- 7
     e_mail VARCHAR(80) NOT NULL CHECK(e_mail LIKE '%@%'),  -- 8
     phone_no BIGINT(10),    -- 9
     pieces INT NOT NULL,    -- 10
     bookname VARCHAR(100) NOT NULL,   -- 11
     order_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 12
     user_name VARCHAR(30) NOT NULL, -- 13
     order_type CHAR(7) NOT NULL CHECK(order_type in ('replace', 'new', 'return')), -- 14
     FOREIGN KEY (ord_no) REFERENCES books(book_id)
	);

ALTER TABLE orders engine = InnoDB;

INSERT INTO orders (ord_no, customer_name, address, district, city, state_ut, pincode, country, e_mail, phone_no, pieces, bookname, order_dt, user_name, order_type)
VALUES
('Swarit', 'C-121, SBI Colony, Main Branch Campus, Opposite Kachahari', 'Varanasi', 'Varanasi', 'Uttar Pradesh', 221002, 'India', 
'swaritjain123@gmail.com', 8004124465, 5, 'american gods', '2020-10-26 15:30:11', 'admin', 'new'),
('Swarit', 'C-121, SBI Colony, Main Branch Campus, Opposite Kachahari', 'Varanasi', 'Varanasi', 'Uttar Pradesh', 221002, 'India', 
'swaritjain123@gmail.com', 8004124465, 1, 'coraline', '2020-11-01 15:30:11', 'admin', 'new'),
(5, 'Swarit', 'C-121, SBI Colony, Main Branch Campus, Opposite Kachahari', 'Varanasi', 'Varanasi', 'Uttar Pradesh', 221002, 'India', 
 'swaritjain123@gmail.com', 8004124465, 2, 'the namesake', '2020-11-02 15:30:11', 'admin', 'return');
 
 -- Orders inserted above are being used in the program to show outputs of replace and return functions with the help of date difference b/w 7 to 14 days
 
-- --------------------------------------------- Accounts Table ---------------------------------------------------------------
CREATE TABLE accounts
	(ID BIGINT PRIMARY KEY AUTO_INCREMENT,
	 username VARCHAR(30) UNIQUE NOT NULL,
	 passwd VARCHAR(40) NOT NULL,
     name_u VARCHAR(50) NOT NULL, 
     email VARCHAR(50) UNIQUE NOT NULL CHECK(email LIKE '%@%') 
     );

-- ------------------------------------------------------------------------------------------------------------------------------

-- ----------------------------------------------- Test Accounts ----------------------------------------------------------------

INSERT INTO accounts (username, passwd, name_u, email)
VALUES
('admin', 'admin', 'admin', 'swaritjain123@gmail.com'),
('testuser', 'testuser', 'test', 'tanishq.rc@gmail.com');

ALTER TABLE accounts engine = InnoDB;
-- -------------------------------------------------------------------------------------------------------------------------------
