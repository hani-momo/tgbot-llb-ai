'''Models.'''
from sqlalchemy import (
    Column, Integer, String, 
    ForeignKey
    )
from sqlalchemy.orm import relationship

from db import Base


class UserDictionary(Base):
    __tablename__ = 'user_dictionary'

    user_id = Column(Integer, primary_key=True)
    dictionary_id = Column(Integer, ForeignKey('dictionary.dictionary_id'))
    dictionary_name = Column(String)
    username = Column(String)
    language = Column(String)

    dictionaries = relationship("Dictionary", back_populates="user_dictionaries")


class Dictionary(Base):
    __tablename__ = 'dictionary'

    dictionary_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_dictionary.user_id'))
    original_word = Column(String)
    native_word = Column(String)

    user_dictionaries = relationship("UserDictionary", back_populates="dictionaries")


# Table user_dictionary {
#   user_id integer [primary key]
#   dictionary_id integer [ref: > dictionary.dictionary_id]
#   dictionary_name varchar
#   username varchar
#   language varchar // ch - ru
# }

# Table dictionary {  
#   user_id integer [ref: > user_dictionary.user_id]
#   dictionary_id integer [primary key]
#   original_word varchar
#   native_word varchar
# }
