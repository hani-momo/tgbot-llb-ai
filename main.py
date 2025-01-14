'''Registry for message handlers with filters to pass.'''
import logging

from telebot import types

from bot import bot

from ai import build_prompt, get_completion, conversation_history


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUPPORTED_LANGUAGES = ['Chinese', 'Polish', 'Spanish', 'French', 'Italian', 'German']
MOCK_USER_DICTIONARIES = {
            'My favorite dictionary':{}, # word: translation
            'Chinese dictionary':{}, 
            'Polish food words':{},
            'Italian pasta dictionary':{},
        }

def greet_in_chosen_language(learning_language: str) -> tuple[str, str]:
    greetings = {
        "Chinese": "你好",
        "Polish": "Cześć",
        "Spanish": "Hola",
        "French": "Bonjour",
        "Italian": "Ciao",
        "German": "Hallo",
    }
    greeting = greetings.get(learning_language)
    return greeting


@bot.message_handler(commands=['start'])
def to_select_learning_language(message):
    '''Select learning language.'''
    keyboard = types.InlineKeyboardMarkup()

    for lang in SUPPORTED_LANGUAGES:
        keyboard.add(
            types.InlineKeyboardButton(
                text=lang, callback_data=f"learning_lang:{lang}"
                )
            )

    intro_message = "Hello! I am your Language Learning Buddy. \nI can help you learn new languages in a fun and interactive way! \nWhat language do you want to learn first?"
    bot.send_message(message.chat.id, intro_message, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('learning_lang:'))
def handle_greet_in_learning_language(call):
    '''Greet user in chosen learning language.'''
    learning_language = call.data.split(':')[1]
    user_id = call.from_user.id

    conversation_history[user_id] = {"learning_language": learning_language}

    greeting_in_learning_language = greet_in_chosen_language(learning_language)
    bot.send_message(call.message.chat.id, f"<b>{greeting_in_learning_language}</b>! That's how you say \"Hello\" in {learning_language}. \nTo save the word in <b>dictionary</b> use <b>/neword</b>", parse_mode="HTML")


@bot.message_handler(commands=['neword'])
def to_create_new_word(message):
    '''
    Handles selection of dictionary to where to save the new word.
    '''
    keyboard = types.InlineKeyboardMarkup()
    for d in MOCK_USER_DICTIONARIES:
        keyboard.add(
            types.InlineKeyboardButton(
                text=d, callback_data=f"dictionary:{d}"
                )
            )

    keyboard.add(
        types.InlineKeyboardButton(
            text="Create New Dictionary", callback_data="new_dictionary"
            )
        )
    bot.send_message(message.chat.id, text="<b>Select a dictionary or create</b> a new one to save the new word to:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "new_dictionary")
def handle_new_dictionary_name(call):
    '''Gets the new dictionary name.'''
    msg = bot.send_message(call.message.chat.id, "Enter new dictionary name:")
    bot.register_next_step_handler(msg, handle_create_dictionary)

def handle_create_dictionary(message):
    '''Util, creates the dictionary and prompt for the word and translation.'''
    new_dictionary_name = message.text.strip()

    if not new_dictionary_name:
        bot.send_message(message.chat.id, "Dictionary name cannot be empty. Try again:")
        return

    if new_dictionary_name in MOCK_USER_DICTIONARIES:
        bot.send_message(message.chat.id, "A dictionary with that name already exists. Please choose another name.")
        return

    MOCK_USER_DICTIONARIES[new_dictionary_name] = {}

    msg = bot.send_message(message.chat.id, f"Enter <b>word:translation</b> to add to {new_dictionary_name}:", parse_mode="HTML")
    bot.register_next_step_handler(msg, handle_save_word, new_dictionary_name)


@bot.callback_query_handler(func=lambda call: call.data.startswith('dictionary:'))
def handle_select_existing_dictionary(call):
    '''Handle selecting an existing dictionary.'''
    chosen_dictionary = call.data.split(':', 1)[1]
    msg = bot.send_message(call.message.chat.id, f"Enter <b>word:translation</b> to add to {chosen_dictionary}:", parse_mode="HTML")
    bot.register_next_step_handler(msg, handle_save_word, chosen_dictionary)

def handle_save_word(message, chosen_dictionary):
    '''Save the new word and translation to chosen dictionary.'''
    word_added = False
    while not word_added:
        try:
            word, translation = message.text.split(':', 1)
            word = word.strip().lower()
            translation = translation.strip()

            msg = bot.reply_to(message, f"Enter <b>word:translation</b> to add to {chosen_dictionary}:", parse_mode="HTML")

            if not word or not translation:
                bot.send_message(message.chat.id, "Word and translation cannot be empty. Please use the 'word:translation' format.")
                bot.register_next_step_handler(msg, handle_save_word, chosen_dictionary)
                return

            if word in MOCK_USER_DICTIONARIES[chosen_dictionary]:
                bot.send_message(message.chat.id, "Word already exists in this dictionary.  Please enter a different word.")
                bot.register_next_step_handler(msg, handle_save_word, chosen_dictionary)
                return

            MOCK_USER_DICTIONARIES[chosen_dictionary][word] = translation
            bot.send_message(
                message.chat.id,
                f"Added <b>'{word}':'{translation}' to {chosen_dictionary}</b>. \nTo view saved dictionaries use <b>/dicts</b>.", parse_mode="HTML")
            word_added = True

        except (ValueError, KeyError):
            bot.send_message(message.chat.id, "Invalid input. Please use the 'word:translation' format.")
            bot.register_next_step_handler(msg, handle_save_word, chosen_dictionary)
            return

        except Exception as e:
            logging.error(f"Error saving word: {e}")
            bot.send_message(message.chat.id, "An error occurred.")
            break


@bot.message_handler(commands=['dicts'])
def handle_list_dictionaries(message):
    '''Lists user's dictionaries.'''
    if not MOCK_USER_DICTIONARIES:
        bot.send_message(message.chat.id, "No dictionaries available yet.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for dictionary_name in MOCK_USER_DICTIONARIES:
        keyboard.add(
            types.InlineKeyboardButton(
                text=dictionary_name, callback_data=f"list_words:{dictionary_name}"
            )
        )
    bot.send_message(message.chat.id, "Choose a dictionary to view:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('list_words:'))
def handle_list_words(call):
    '''Lists words in chosen dictionary.'''
    chosen_dictionary = call.data.split(':', 1)[1]

    try:
        words = MOCK_USER_DICTIONARIES[chosen_dictionary]
        if not words:
            bot.send_message(call.message.chat.id, f"{chosen_dictionary} is empty.")
            return

        word_list = "\n".join([f"<b>{word}</b>: {translation}" for word, translation in words.items()])
        bot.send_message(call.message.chat.id, f"{chosen_dictionary}:\n{word_list}", parse_mode="HTML")

    except KeyError:
        bot.send_message(call.message.chat.id, "Dictionary not found.")


@bot.message_handler(commands=['chat'])
def to_chat(message, in_chat=False):
    '''Chat with AI Model.'''
    user_id = message.from_user.id
    user_input = message.text

    if user_id not in conversation_history or 'learning_language' not in conversation_history[user_id]:
        bot.send_message(message.chat.id, "Select a language first using /start.")
        return

    learning_language = conversation_history[user_id]['learning_language']

    if 'messages' not in conversation_history[user_id]:
        conversation_history[user_id]['messages'] = []

    if not user_input.startswith("/chat"):
        conversation_history[user_id]['messages'].append({"role": "user", "content": user_input})

    prompt = build_prompt(conversation_history[user_id]['messages'], learning_language)
    response = get_completion(prompt=prompt)
    response = response.replace("assistant:", "").strip()

    conversation_history[user_id]['messages'].append({"role": "assistant", "content": response})
    bot.send_message(message.chat.id, response)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_chat_continuation(message):
    if message.text.startswith('/'):
        '''Command handlers handle the commands'''
        return

    user_id = message.from_user.id
    if user_id in conversation_history and 'messages' in conversation_history[user_id]:
        '''Continue chat if not commands'''
        to_chat(message)
    else:
        unknown_command(message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def unknown_command(message):
    '''Debugging message handler, processes non-command messages'''
    bot.reply_to(message, "I don't understand that command.  Try /help for a list of available commands.")


bot.infinity_polling()