def lowInformation(dic, length):
    if (len(dic) < 50):
        return True
    else:
        top15 = 0
        counter = Counter(dic)
        most_common_words = counter.most_common(15)
        for i in range(15):
            top15 += most_common_words[i][1]
        if ((top15 / length) > 0.6):
            return True
        else:
            return False