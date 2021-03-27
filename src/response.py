from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from src import Base


class Response(Base):
    id = Column(Integer, primary_key=True)
    question = Column(Integer)
    user = Column(Integer, ForeignKey("users.id"))
    answer = Column(String(127))
    datetime = Column(DateTime)

    __tablename__ = "responses"

    def __init__(self, question, user, answer, current_datetime):
        self.question = question
        self.user = user
        self.answer = answer
        self.datetime = current_datetime

    def __repr__(self):
        return f"Question: {self.id}\n" \
               f"User: {self.user}\n" \
               f"Answer: {self.answer}\n" \
               f"Datetime: {self.datetime}"
