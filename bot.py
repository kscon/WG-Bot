import logging
import pandas as pd
import datetime
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext
)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from apikey import API_KEY

logging.basicConfig(
    filename='wgbot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

TRASH, MORETRASH = range(2)

reply_keyboard = [['Biomüll', 'Restmüll', 'Gelber Sack','WC-Müll', 'Papiermüll'],
                      ['Fertig', 'Abbruch']]

"""
def start(update, context):
    # Send a message when the command /start is issued
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hi!')
    logger.info("Bot was started")

    # print(update.effective_chat.id)

    putzplan_reminder(update, context)
    logger.info('Putzplan reminder was started')
"""


# method for reading the putzplan.csv file. Do read all entries, a deletion of very old entries is done in an separate
# method
def read_putzplan_csv(filestring):
    df = pd.read_csv(filestring, delimiter=';', parse_dates=True, dayfirst=True)
    df.index = pd.DatetimeIndex(df.Woche, dayfirst=True)
    df = df.drop(['Woche'], axis=1)
    # today = pd.Timestamp.today() - pd.to_timedelta('7d')
    # return df[df.index > today][:4]
    return df


def generate_putzplan():
    # generate new putzplan for the current year. Last eneNEN
    df = read_putzplan_csv('putzplan.csv')
    ln1 = df.loc[df.index[-1], 'Name']
    ln2 = df.loc[df.index[-2], 'Name']
    ln3 = df.loc[df.index[-3], 'Name']
    names = [ln3, ln2, ln1]
    counter = 0
    while (df[-1:].index.year == pd.Timestamp.today().year):
        last_entry_index = df.index[-1]
        date_to_add = last_entry_index + pd.to_timedelta('7d')
        df = df.append(pd.Series(data={'Name': names[counter]}, name=date_to_add))

        # cycle through the name list
        counter = (counter + 1) % 3

    logger.info('Putzplan for the current year was generated')

    # print(df.head())

    # ('debug:',df.loc[df.index[-1], 'Name'])  #df['Woche'][lw.strftime('%Y-%m-%d')])
    df.to_csv('putzplan.csv', sep=';', date_format='%d.%m.%Y')
    logger.info('Putzplan.csv was extended by new entries')
    return df


def generate_new_year_putzplan():
    df = read_putzplan_csv('putzplan.csv')
    try:
        assert len(df.index) > 52
    except:
        logger('Generating_new_year_putzplan() only works with a correct csv file.')
        return
    print('Check!')


def putzplan(update, context):
    """df = pd.read_csv("pp.csv", delimiter=';', parse_dates=True, dayfirst=True)
    df.index = pd.DatetimeIndex(df.Woche, dayfirst=True)
    df = df.drop(['Woche'], axis=1)
    today = pd.Timestamp.today() - pd.to_timedelta('7d')
    df = df[df.index > today][:4]"""
    df = read_putzplan_csv('putzplan.csv')

    # check if putzplan is not completely set for the current year
    if len(df.index) < 50:
        logger.info('current putzplan is not set for the complete year')
        generate_putzplan()
        df = read_putzplan_csv('putzplan.csv')

    # get putzplan for the next 4 week including the current week
    last_week = pd.Timestamp.today() - pd.to_timedelta('7d')
    df_next_month = df[df.index > last_week][:4]

    output = df_next_month.to_string(index=True, justify='left', col_space=15). \
        replace('Name', '').replace('Woche', '').strip().split()

    output[1] = output[1] + '   <'
    s = ''
    for i in range(len(output)):
        s += output[i]
        if i % 2 == 1:
            s += '\n'
        else:
            s += '   '
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=s)


def send_putzplan_reminder(context):
    df = read_putzplan_csv('putzplan.csv')
    last_week = pd.Timestamp.today() - pd.to_timedelta('7d')
    df = df[df.index > last_week]
    current_name = df.loc[df.index[0], 'Name']
    # current_name = df.loc[df.index[-1], 'Name']
    output = "Hallo liebe WG, bitte vergesst das Putzen nicht! \nDiese Woche ist " + current_name + " dran ;)"
    context.bot.send_message(chat_id=context.job.context, text=output)


"""
def putzplan_reminder(chat_id):
    context.job_queue.run_daily(send_putzplan_reminder, context=update.message.chat_id, days=(6, 6),
                                time=datetime.time(hour=9, minute=0, second=0))

    # debugging timestamp
    # context.job_queue.run_daily(send_putzplan_reminder, context=update.message.chat_id, days=(6, 6),
    #                            time=datetime.time(hour=12, minute=40, second=30))
"""


def log(update, context):
    # display the content of the log file
    log_text = ''
    with open('wgbot.log', 'r') as f:
        for line in (f.readlines()[-10:]):
            log_text += line  # + '\n'

    logger.info('Log was read')

    context.bot.send_message(chat_id=update.effective_chat.id, text=log_text)


def money_print(update, context):
    # method for displaying current balance
    df = read_money_balance()
    input = df.to_string(index=True, justify='right', col_space=15).replace('Name', '').strip().split()
    star = '*'
    output = f"{star:15} {input[0]:20} {input[1]:12} {input[2]:8} \n"
    output += f"{input[3]:15} {input[4]:12.7} {input[5]:20.7} {input[6]:12.7} \n"
    output += f"{input[7]:20} {input[8]:12.7} {input[9]:20.7} {input[10]:12.7} \n"
    output += f"{input[11]:14} {input[12]:12.7} {input[13]:20.7} {input[14]:12.7} \n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    logger.info('money_balance was read')


def money_transactions(update, context):
    df = read_money_transactions()
    df = df[-10:]
    output = df.to_string(index=True, justify='right', col_space=15)
    output = 'nr' + output
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    logger.info('transaction was read')


def read_money_balance():
    return pd.read_csv('balance.csv', delimiter=';', index_col=0)


def read_money_transactions():
    return pd.read_csv('transactions.csv', delimiter=';')


def money_add_transaction(update, context):
    # add an transaction to the record
    try:
        # check if names are valid
        if not check_name_valid(context.args[0]) or ((not check_name_valid(context.args[1])) and
                                                     (not (context.args[1] == '*'))):
            context.bot.send_message(chat_id=update.effective_chat.id, text="The name you entered is not valid!")
            return

        # check if a reason was given
        reason = '-'
        try:
            reason = str(context.args[3])
        except:
            pass

        try:
            amount = context.args[2].replace(',', '.')
            value = round(float(amount), 2)
        except Exception as e:
            logger.info('Exception while converting the value happened!')
            logger.info(str(e))
            context.bot.send_message(chat_id=update.effective_chat.id, text="Exception while \
                            converting the value happened!")
            return

        # df = read_money_transactions()
        if context.args[1] == '*':
            name_list = get_list_of_names()
            name_list.remove(context.args[0])
            for n in name_list:
                # df = df.append({'name': context.args[0], 'target': n, 'amount': value}, ignore_index=True)
                write_transaction_to_file(context.args[0], n, value, reason)
        else:
            # df = df.append({'name': context.args[0], 'target': context.args[1], 'amount': value}, ignore_index=True)
            write_transaction_to_file(context.args[0], context.args[1], value, reason)
        # df.to_csv('transactions.csv', sep=';', index=False)

        try:
            if context.args[1] == '*':
                name_list = get_list_of_names()
                name_list.remove(context.args[0])
                for n in name_list:
                    money_recalculate_balance(context.args[0], n, value)
                    money_recalculate_balance(n, context.args[0], -value)
            else:
                # recalculate balance twice to make matrix symmetric
                money_recalculate_balance(context.args[0], context.args[1], value)
                money_recalculate_balance(context.args[1], context.args[0], -value)
        except Exception as e:
            logger.info('Exception while recalculating the balance!')
            context.bot.send_message(chat_id=update.effective_chat.id, text="Error while recalculating the balance!")
            return

        transaction = context.args[0] + ' ' + context.args[1] + ' ' + str(value)
        logger.info('transaction ' + transaction + ' was added')
        context.bot.send_message(chat_id=update.effective_chat.id, text="Transaction was successfully added!")
        money_print(update, context)

    except (IndexError, ValueError):
        logger.info('Exception in adding transaction happened')
        context.bot.send_message(chat_id=update.effective_chat.id, text="Error! \nUsage: \
            /money_record <demander> <target> <value> (<reason>)")


def write_transaction_to_file(name, target, amount, reason):
    df = read_money_transactions()
    df = df.append({'name': name, 'target': target, 'amount': amount, 'reason': reason}, ignore_index=True)
    df.to_csv('transactions.csv', sep=';', index=False)


def get_list_of_names():
    name_list = []
    with open('listofnames.txt', 'r') as f:
        name_list = f.read().strip().split()
    return name_list


def check_name_valid(name):
    name_list = get_list_of_names()
    if name in name_list:
        return True
    else:
        return False


def money_recalculate_balance(name, target, amount):
    df = read_money_balance()
    df.loc[name, target] = round(df.loc[name, target] + amount, 2)
    df.to_csv('balance.csv', sep=';', index=True)


def money_wants(update, context):
    # method for easier reading the balance matrix
    try:
        name = context.args[0]
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Not a valid name!")
        logger.info('no name was provided for command money_debt')
    if not check_name_valid(name):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Not a valid name!")
        logger.info('attempt was made to output debt from not exisiting name')

    df = read_money_balance()
    df = df.loc[name, :]

    # print(df.to_string())

    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string())
    logger.info('money_balance was read')


# method is unecessary if balance matrix is symmetric
"""def money_clean_balance():
    name_list = get_list_of_names()
    df = read_money_balance()

    for i in name_list:
        for j in name_list:
            if not i == j:
                value1 = df.loc[i,j]
  """

# ---- Trash ----- #

def trash_conversation(update, context):
    update.message.reply_text('Welchen Müll willst du runterbringen?',
                              reply_markup = ReplyKeyboardMarkup(
                                    reply_keyboard, one_time_keyboard=True, input_field_placeholder='Müll?')
                              )
    user = update.message.from_user
    update.message.reply_text(user.first_name + ' test ' + update.messsage.text,  reply_markup=ReplyKeyboardRemove())

def trash_conversation_continue(update, context):
    pass

def trash_conversation_done(update, context):
    pass

"""

def trash_message(context):
    if 'b' in context.job.context:
        output = "Hallo liebe WG, bitte einmal den Biomüll runterbringen!"
    elif 'r' in context.job.context:
        output = "Hallo liebe WG, bitte einmal den Restmüll runterbringen!"
    elif 'g' in context.job.context:
        output = "Hallo liebe WG, bitte einmal den gelben Sack runterbringen!"
    elif 'w' in context.job.context:
        output = "Hallo liebe WG, bitte einmal den Badezimmermüll runterbringen!"
    elif 'p' in context.job.context:
        output = "Hallo liebe WG, bitte einmal den Papiermüll runterbringen!"
    context.bot.send_message(chat_id=context.job.context[0], text=output)


# Trash
# Gelber Sack -> g
# Restmüll -> r
# Biomüll -> b
# WC-Müll -> w
# Papier -> p
def activate_trash(job_queue, group_chat_id):
    job_queue.run_repeating(trash_message, interval=datetime.timedelta(days=3), first=datetime.timedelta(days=3),
                            name='trash_b', context=[group_chat_id, 'b'])
    job_queue.run_repeating(trash_message, interval=datetime.timedelta(days=4), first=datetime.timedelta(days=4),
                            name='trash_b', context=[group_chat_id, 'r'])
    job_queue.run_repeating(trash_message, interval=datetime.timedelta(days=8), first=datetime.timedelta(days=8),
                            name='trash_b', context=[group_chat_id, 'g'])
    job_queue.run_repeating(trash_message, interval=datetime.timedelta(days=13), first=datetime.timedelta(days=4),
                            name='trash_b', context=[group_chat_id, 'w'])
    job_queue.run_repeating(trash_message, interval=datetime.timedelta(days=10), first=datetime.timedelta(days=3),
                            name='trash_b', context=[group_chat_id, 'p'])

"""


def print_help(update, context):
    output = 'List of commands:\n'
    output = output + '/putzplan => show current putzplan\n'
    output = output + '/money_print (/mp) => show current money balances\n'
    output = output + '/money_record (/mr) => record a transaction\n'
    output = output + '/money_wants (/mw) => show current balances for one person\n'
    output = output + '/money_transactions (/mt) => show list of last added transactions\n'
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    logger.info('help was issued')


def main():
    # initialize stuff
    updater = Updater(API_KEY, use_context=True)
    jq = updater.job_queue

    # introduce dispatcher locally
    dp = updater.dispatcher

    group_chat_id = 0

    chat_ids = []
    with open('chatids.txt', 'r') as f:
        text = f.read().strip().split()
        for t in text:
            chat_ids.append(int(t))

    chat_ids_all = []
    with open('chatids_all.txt', 'r') as f:
        text = f.read().strip().split()
        for t in text:
            chat_ids_all.append(int(t))
            if t[0] == '-':
                group_chat_id = t

    filter = Filters.chat(chat_id=chat_ids)
    filter_all = Filters.chat(chat_id=chat_ids_all)
    # dp.add_handler(CommandHandler("start", start, filter))
    dp.add_handler(CommandHandler('putzplan', putzplan, filter_all))
    dp.add_handler(CommandHandler('log', log, filter_all))
    dp.add_handler(CommandHandler('money_print', money_print, filter_all))
    dp.add_handler(CommandHandler('money_record', money_add_transaction, filter_all))
    dp.add_handler(CommandHandler('money_wants', money_wants, filter_all))
    dp.add_handler(CommandHandler('money_transactions', money_transactions, filter_all))
    dp.add_handler(CommandHandler('help', print_help, filter_all))

    # trash
    #dp.add_handler(CommandHandler('trash', trash_conversation, filter_all))

    # abbreviations
    dp.add_handler(CommandHandler('mp', money_print, filter_all))
    dp.add_handler(CommandHandler('mr', money_add_transaction, filter_all))
    dp.add_handler(CommandHandler('mw', money_wants, filter_all))
    dp.add_handler(CommandHandler('mt', money_transactions, filter_all))

    # start putzplan reminder
    jq.run_daily(send_putzplan_reminder, context=group_chat_id, days=(6, 6),
                 time=datetime.time(hour=9, minute=0, second=0))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('trash', trash_conversation)],
        states={
            TRASH: [
                MessageHandler(
                    Filters.regex('^(Biomüll|Restmüll|Gelber Sack|WC-Müll|Papiermüll)$'), trash_conversation_continue
                ),
                MessageHandler(Filters.regex('^(Fertig)'), trash_conversation_continue),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Abbruch'), trash_conversation_done)],
    )

    # start trash reminder
    # activate_trash(jq, group_chat_id)

    logger.info("Started bot")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
