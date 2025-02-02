for keyword in ["overflow", "memory", "dos", "privileges", "rce"]:
    keywords = ["if", "else", "for", "while", "free", "+", "-", "/", " * ", "&", "&&", "continue", "break", "goto", "return", "NULL", "#define", "|", "||", ">=", "=", "<=", "!="] #, "bool", "integer", "long", "float", "true", "false"]
    keywords_good = {}
    with open(keyword+"_good.txt", "r+") as good:
        for line in good.readlines():
            for word in keywords:
                if word in line:
                    if word not in keywords_good.keys():
                        keywords_good[word] = 1.0
                    else:
                        keywords_good[word] += 1.0
    print(keywords_good)

    keywords_bad = {}
    with open(keyword+"_bad.txt", "r+") as bad:
        for line in bad.readlines():
            for word in keywords:
                if word in line:
                    if word not in keywords_bad.keys():
                        keywords_bad[word] = 1.0
                    else:
                        keywords_bad[word] += 1.0
    print(keywords_bad)

    weights = {}
    
    for key in keywords_good.keys():
        if key in keywords_bad.keys():
            weights[key] = keywords_good[key] / keywords_bad[key]
    
    with open("Weights/"+keyword+"_weights.txt", "w+") as weightfile:
        for keyword, weight in weights.items():
            weightfile.write(str(keyword) + "  " + str(weight) + "\n")
    
