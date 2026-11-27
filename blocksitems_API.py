import requests

url = "https://blocksitems.com/api/2026.1.3"
userinputcat = ""
userinputend = "No"
categories = ["Items", "Blocks", "Mods", "Modpacks", "All"]


def showfounddata():
    datenlange = len(data["data"])
    for i in range(datenlange):
        if userinputcat != "All":
            print(f"{userinputcat.strip("s")}: {data["data"][i]["display_name"]}\n")
        else:
            print(f"{cat.strip("s")}: {data["data"][i]["display_name"]}\n")

        match userinputcat:
            case "Items" | "Blocks":
                print(f"Mod: {data["data"][i]["mod"]["display_name"]}\n")
            case "Mods":
                print(f"Mod: {data["data"][i]["display_name"]}\nLoader:{data["data"][i]["loaders"]}\n")
            case "Modpacks":
                print(f"Mod count: {data["data"][i]["mod_count"]}\nDiscription:{data["data"][i]["summary"]}\n")
                
        match userinputcat:
            case "Items" | "Blocks" | "Mods":
                print(f"Versions: ")
                for j in data["data"][i]["mc_versions"]:
                    print(j)
            case "Modpacks":
                print(f"Version: ")
                print(data["data"][i]["mc_version"])  
        print("\n")

# =============================================================================
# ADDED __NAME__ CHECK FOR GUI: Only run the terminal loop when this file is run directly,
# so importing blocksitems_API in blocksitems_GUI.py does not block on input().
# =============================================================================
if __name__ == "__main__":
# =============================================================================
# END OF CODE ADDED FOR GUI
# =============================================================================
    while True:
        while userinputcat not in categories:
            userinputcat = input("What are you looking for?\nItems, Blocks, Mods, Modpacks, All\n")

        if userinputcat != "All":

            userinput = input(f"What {userinputcat.strip("s")} are you looking for?\n")
            url = "https://blocksitems.com/api/2026.1.3/" + userinputcat.lower() + "?q=" + userinput.lower()
            data = requests.get(url)
            data = data.json()
            showfounddata()


        else:
            userinput = input(f"What are you looking for?\n")

            for cat in categories:
                if cat != "All":
                    url = "https://blocksitems.com/api/2026.1.3/" + cat.lower() + "?q=" + userinput.lower() + "&scope=all"
                    print(f"{cat}:\n")
                    data = requests.get(url)
                    data = data.json()
                    showfounddata()
        
        userinputend = "No"

        while userinputend != "Yes":
            
            if userinputcat != "All":
                userinputpage = input(userinputcat + " per page: " + str(data["pagination"]["limit"]) + "\nCurrent Page: " + str(data["pagination"]["page"]) + "\nPages: " + str(data["pagination"]["pages"]) + "\nGo to Page: ")
            else:
                userinputpage = input(cat + " per page: " + str(data["pagination"]["limit"]) + "\nCurrent Page: " + str(data["pagination"]["page"]) + "\nPages: " + str(data["pagination"]["pages"]) + "\nGo to Page: ")
            
            if userinputpage.isdigit():

                if int(userinputpage) <= data["pagination"]["pages"]:

                    if "&page=" in url: 
                        url = url.replace("&page=" + str(data["pagination"]["page"]), "&page=" + str(userinputpage))
                    
                    else:
                        url = url + "&page=" + str(userinputpage)
                    data = requests.get(url)
                    data = data.json()
                    showfounddata()

                else:
                    print("Invalid page number, Type a number between 1 and " + str(data["pagination"]["pages"]))
                    userinputend = input("Do you want to search for something else?\nYes No\n")
                    
            if userinputpage.isdigit() == False:
                userinputend = input("Do you want to search for something else?\nYes No\n")
            if userinputend == "Yes":
                userinputcat = ""