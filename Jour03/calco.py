import tkinter as tk
import math
import ast
import operator
import re  

#----------------- VARIABLES GLOBALES ----------------
etat_exp = False
af_his = False
history = []
long = 0

#----------------- MOTEUR DE CALCUL (AST) ----------------
OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
}

FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log10, "ln": math.log,
    "exp": math.exp,
}

CONSTANTS = { "pi": math.pi, "e": math.e }

def safe_eval(expr):
    """Évalue une expression mathématique de manière sécurisée"""
    def eval_node(node):
        if isinstance(node, ast.Constant): return node.value
        elif isinstance(node, ast.Num): return node.n
        elif isinstance(node, ast.BinOp):
            return OPERATORS[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return OPERATORS[type(node.op)](eval_node(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in FUNCTIONS:
                return FUNCTIONS[func_name](eval_node(node.args[0]))
            else: raise ValueError("Fonction inconnue")
        elif isinstance(node, ast.Name):
            if node.id in CONSTANTS: return CONSTANTS[node.id]
            
        raise ValueError("Erreur de syntaxe")

    try:
        # On essaie d'évaluer
        tree = ast.parse(expr, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        raise e

#----------------- FONCTIONS INTERFACE ----------------

def clear(ecran):
    global etat_exp, af_his
    ecran.delete(0, tk.END)
    ecran.insert(0, "0")
    etat_exp = False
    af_his = False

def back(ecran):
    current = ecran.get()
    if len(current) > 1 and current != "Erreur":
        ecran.delete(len(current)-1, tk.END)
    else:
        clear(ecran)

# --- TON SYSTEME DE NAVIGATION (Restauré) ---
def nav(ecran, txt):
    global af_his, long, etat_exp
    
    if txt == '⬆️' and history:
        if not af_his:
            long = len(history) - 1 
            af_his = True
        else:
            long -= 1
            if long < 0:
                long = len(history) - 1
        ecran.delete(0, tk.END)
        ecran.insert(tk.END, history[long]) # Affiche tout l'historique
        etat_exp = False # Important pour pouvoir réécrire par dessus

    elif txt == '⬇️' and history:
        if not af_his:
            long = 0
            af_his = True
        else:
            long += 1
            if long >= len(history):
                long = 0
        ecran.delete(0, tk.END)
        ecran.insert(tk.END, history[long])
        etat_exp = False

    elif txt == '⬅️':
        # J'ai gardé ta logique, mais j'ai ajouté back()
        if etat_exp:    
            back(ecran)
        else:
            # Si on n'est pas en cours d'édition (ex: résultat affiché), on efface tout
            clear(ecran)
            
    elif txt == '©️':
        clear(ecran)

def clique(ecran, text):
    global etat_exp, af_his
    current_text = ecran.get()

    # --- Factoriel (!) ---
    if text == '!':
        try:
            if "=" in current_text: 
                current_text = current_text.split(" = ")[1]
            
            val = int(safe_eval(current_text))
            res = math.factorial(val)
            ecran.delete(0, tk.END)
            ecran.insert(tk.END, str(res))
            history.append(f"{current_text}! = {res}")
            etat_exp = False
            af_his = False
        except:
            ecran.delete(0, tk.END)
            ecran.insert(tk.END, "Erreur")
        return

    if text == '=':
        try:
            expression = current_text
            
            if "=" in expression:
                expression = expression.split(" = ")[1]

            
            expression = expression.replace('^', '**')
            expression = expression.replace('π', 'pi')
            expression = expression.replace('√', 'sqrt') 
            expression = expression.replace('sin⁻¹', 'asin')
            expression = expression.replace('cos⁻¹', 'acos')
            expression = expression.replace('tan⁻¹', 'atan')
            
            
            pattern = r'(sqrt|sin|cos|tan|log|ln|asin|acos|atan|exp)(\d+(\.\d+)?)'
            expression = re.sub(pattern, r'\1(\2)', expression)
            
            result = safe_eval(expression)
            
            ecran.delete(0, tk.END)
            ecran.insert(tk.END, str(result))
            
            # Ajout à l'historique
            history.append(f"{expression.replace('**','^').replace('sqrt','√')} = {result}")
            
            etat_exp = False
            af_his = False

        except Exception as ex:
            ecran.delete(0, tk.END)
            ecran.insert(tk.END, "Erreur")
            print(ex)
            etat_exp = False
        return

    # --- Saisie Normale ---
    if af_his:
        af_his = False
        if text not in ['+', '-', '*', '/', '^', ')', '.']: 
            ecran.delete(0, tk.END)
        etat_exp = True
        
    elif not etat_exp or current_text == "0" or current_text == "Erreur":
        if text not in ['+', '-', '*', '/', '^', ')', '.']: 
            ecran.delete(0, tk.END)
        etat_exp = True

    ecran.insert(tk.END, text)

#------------------ INTERFACE GRAPHIQUE ----------------
fennetre = tk.Tk()
fennetre.title("Calculatrice KVJ")
fennetre.geometry("400x600")
fennetre.configure(bg="#280202")

label = tk.Label(fennetre, text="Calculatrice Scientifique", font=('Arial', 12), bg="#4C9220", fg="white")
label.grid(row=0, column=0, columnspan=4, pady=5, sticky="ew")

ecran = tk.Entry(fennetre, font=('Arial', 24), borderwidth=2, relief='ridge', justify="right")
ecran.insert(0, "0")
ecran.grid(row=1, column=0, columnspan=4, padx=10, pady=15, sticky="nsew")

# --- Boutons Navigation (Ton système) ---
b_nav = ['⬆️','⬇️','⬅️', '©️']
for i, text in enumerate(b_nav): 
    tk.Button(fennetre, text=text, width=4, height=2, bg="#D9534F", fg="white", 
              command=lambda t=text: nav(ecran, t)).grid(row=2, column=i, padx=3, pady=3, sticky="nsew")

# --- Boutons Spéciaux ---
bt_spc = ['sin', 'cos', 'tan', 'log', 'sin⁻¹', 'cos⁻¹', 'tan⁻¹', 'exp', '^', '√','π' , 'ln', 'e', '(',')','!' ]
for i, text in enumerate(bt_spc):
    tk.Button(fennetre, text=text, width=5, height=2, bg="black", fg="white",
              command=lambda t=text: clique(ecran, t)).grid(row=(i//4)+3, column=i%4, padx=5, pady=5, sticky="nsew")

# --- Boutons Chiffres ---
bouttons = ['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', '=', '+']
for i, text in enumerate(bouttons):
    c = "orange" if text == '=' else "#0078D7"
    tk.Button(fennetre, text=text, width=5, height=2, bg=c, fg="white",
              command=lambda t=text: clique(ecran, t)).grid(row=(i//4)+7, column=i%4, padx=5, pady=5, sticky="nsew")

# --- Configuration Grille ---
for i in range(11): fennetre.rowconfigure(i, weight=1)
for i in range(4): fennetre.columnconfigure(i, weight=1)

fennetre.mainloop()