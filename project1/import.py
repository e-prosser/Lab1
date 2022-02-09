import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Initiate database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
  b = open("books.csv")
  reader = csv.reader(b)

  for isbn, name, author, year in reader:
      db.execute("INSERT INTO BOOKS (isbn, name, author, year) VALUES (:isbn, :name, :author, :year)", {"isbn": isbn, "name": name, "author": author, "year": year})
      print(f"Added book named: {name}, ISBN: {isbn}, Author: {author}, Year: {year}")

  db.commit()


if __name__=="__main__":
    main()
