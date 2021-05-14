import pickle
import pandas as pd
from pprint import pprint
from collections import Counter, defaultdict
import json


def to_d3_json(m_dict):
    d3_json = {'nodes': [], 'links': []}
    for uid in m_dict['users']:
        d3_json['nodes'].append({'id': m_dict['users'][uid]})

    messages = []
    for m in m_dict['messages']:
        from_user = m_dict['messages'][m]['from']
        to_user = m_dict['messages'][m]['reply_to_user']
        messages.append((from_user, to_user))
    pair_counts = Counter(messages)
    for pair, count in pair_counts.items():
        d3_json['links'].append({"source": pair[0], "target": pair[1], "value": count})

    with open('messages_counts.json', 'w') as outfile:
        json.dump(d3_json, outfile)
    return None


def is_reply(msg_len, time_prev, time, cooldown=10, spm=175, smp_delta=0.2):
    # cooldown - перерыв между сообщениями, "время на подумать"
    # spm - symbols per minute
    # smp_delta - задает интервал вариативности - сообщение занимает написать
    # Проверяем, как быстро появилось следующее сообщение
    # Для этого считаем, сколько времени теоретически потребовалось, чтобы его написать
    # И сравниваем с тем, сколько потребовалось фактически
    duration = time.second - time_prev.second - cooldown

    predict_len = duration * spm/60
    reply = False
    if (msg_len >= predict_len * (1 - smp_delta))and(msg_len <= predict_len * (1 + smp_delta)):
        reply = True
    return reply


def scan_for_replies(m_dict, is_reply_args):
    c, s, sd = is_reply_args
    m = 0
    pos = 0
    neg = 0
    m_replies = {}
    m_list = list(m_dict.values())
    m_replies[m_list[0]['id']] = m_list[0]
    for n, id in enumerate(m_list[:-1]):
        prev = m_list[n]
        cur = m_list[n+1]
        m_replies[cur['id']] = cur
        if is_reply(cur['text_length'], prev['date'], cur['date'], c, s, sd):
            # Если сообщение появилось так быстро, как появляется ответ, то:
            # - если у оригинального сообщения был адресат, считаем его ответом тому же человеку;
            # - если у сообщений разные авторы, считаем его ответом автору
            if (prev['reply_to_user'] != 'Парк') and (prev['from'] == cur['from']):
                m_replies[cur['id']]['reply_to_user'] = prev['reply_to_user']
            elif prev['from'] != cur['from']:
                if (prev['reply_to_user'] != 'Парк') and (cur['reply_to_user'] != 'Парк'):
                    if m_replies[cur['id']]['reply_to_user'] == prev['from']:
                        # print('+++')
                        # pprint(prev)
                        # pprint(cur)
                        pos += 1
                    else:
                        # print('---')
                        # pprint(prev)
                        # pprint(cur)
                        neg += 1
                m_replies[cur['id']]['reply_to_user'] = prev['from']
            m += 1
    print(f'{c} sec;{s} spm;{sd*100}%; {m} replies; {pos}; {neg}')
    return m_replies


def main():
    messages_dict = pickle.load(open("messages_dict.pickle", "rb"))

    # Тестируем лучшую комбинацию параметров
    for c in [5, 10, 15, 20]:
        for s in [150, 160, 170, 180, 190, 200]:
            for sd in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35]:
                scan_for_replies(messages_dict['messages'], [c, s, sd])
    to_d3_json(messages_dict)


if __name__ == '__main__':
    main()
