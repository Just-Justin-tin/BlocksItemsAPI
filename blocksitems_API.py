import requests

url = "https://blocksitems.com/api/2026.1.3"
userinputcat = ""
categories = ["Items", "Blocks", "Mods", "Modpacks", "All"]


def showfounddata():
    datenlange = len(data["data"])
    if userinputcat != "All":
        for i in range(datenlange):
            print(f"{userinputcat.strip("s")}: {data["data"][i]["display_name"]}\n")
            match userinputcat:
                case "Items" | "Blocks":
                    print(f"Mod: {data["data"][i]["mod"]["display_name"]}\n")
                
                case "Mods":
                    print(f"Mod: {data["data"][i]["display_name"]}\n Loader:{data["data"][i]["loaders"]}\n")

                case "Modpacks":
                    print(f"Mod count: {data["data"][i]["mod_count"]}\n Discription:{data["data"][i]["summary"]}\n")
                
            match userinputcat:
                case "Items" | "Blocks" | "Mods":
                    print(f"Versions: ")
                    for j in data["data"][i]["mc_versions"]:
                        print(j)
                case "Modpacks":
                    print(f"Version: ")
                    print(data["data"][i]["mc_version"])  
            print("\n")
    else:
        for i in range(datenlange):
            match userinputcat:
                case "Items":
                    print(f"Items: {data["data"][i]["display_name"]}\n")
                    print(f"Mod: {data["data"][i]["mod"]["display_name"]}\n")

                case "Blocks":
                    print(f"Blocks: {data["data"][i]["display_name"]}\n")
                    print(f"Mod: {data["data"][i]["mod"]["display_name"]}\n")

                case "Mods":
                    print(f"Mod: {data["data"][i]["display_name"]}\n Loader:{data["data"][i]["loaders"]}\n")

                case "Modpacks":
                    print(f"Modpack: {data["data"][i]["display_name"]}\n")
                    print(f"Mod count: {data["data"][i]["mod_count"]}\n Discription:{data["data"][i]["summary"]}\n")
            
            match userinputcat:
                case "Items" | "Blocks" | "Mods":
                    print(f"Versions: ")
                    for j in data["data"][i]["mc_versions"]:
                        print(j)
                case "Modpacks":
                    print(f"Version: ")
                    print(data["data"][i]["mc_version"])  
            print("\n")

while userinputcat not in categories:
    userinputcat = input("What are you looking for?\n Items, Blocks, Mods, Modpacks, All\n")

if userinputcat != "All":

    userinput = input(f"What {userinputcat.strip("s")} are you looking for?\n")
    url = url + "/" + userinputcat.lower() + "?q=" + userinput.lower()

else:
    userinput = input(f"What are you looking for?")
    for cat in categories:
        if cat != "All":
            url = "https://blocksitems.com/api/2026.1.3/" + cat.lower() + "?q=" + userinput.lower() + "&scope=all"
            data = requests.get(url)
            data = data.json()
            showfounddata()


print(url)


data = requests.get(url)

data = data.json()
# -> Umwandeln von JSON in DICT

showfounddata()

    
while True:
    userinputpage = input(userinputcat + " per page: " + str(data["pagination"]["limit"]) + "\nCurrent Page: " + str(data["pagination"]["page"]) + "\n Pages: " + str(data["pagination"]["total"]) + "\n Go to Page: ")
    if userinputpage == int:
        url = url.replace("?page=" + str(data["pagination"]["page"]), "?page=" + userinputpage)

    elif userinputpage != int:
        userinputend = input("Do you want to search for something else?\n Yes No\n")
        if userinputend == "Yes":
            break
        elif userinputend == "No":
            continue
        
    data = requests.get(url)
    data = data.json()
    
    showfounddata()