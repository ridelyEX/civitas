#this is an easterEgg inside all the applicaation


# Calculadora que hago por diversión en python

def suma(a, b):
    c = a+b
    return c

def resta(a, b):
    c = a-b
    return c

def multiplicación(a, b):
    c = a*b
    return c

def division(a, b):
    c = a/b
    return c

def peso(a):
    if a<=65:
        print("tu peso es normal")
    else:
        print("eres una gorda")
        
def opc():
    print("1. Sumar")
    print("2. Restar")
    print("3. Multiplicar")
    print("4. Dividir")
    print("5. Calculadora de peso")
    print("6. Salir")
    
    opc = input("¿Que deseas hacer? ")
    
    return opc
class calculadora:
    
    q = True
    
    while q == True:
        print("hola, esto es una calculadora ¿que quieres calcular?")
        
        match opc():
            case "1":
                a = input("Ingresa el primer numero: ")
                b = input("Ingrese el segundo numero: ")
                try:
                    a = int(a)
                    b = int(b)
                except ValueError:
                    print("los valores no son números")
                print("La suma de ", a, " + ", b, " es: ", suma(a,b))
            case "2":
                a = input("Ingresa el primer numero: ")
                b = input("Ingrese el segundo numero: ")
                try:
                    a = int(a)
                    b = int(b)
                except ValueError:
                    print("los valores no son números")
                print("La resta de ", a, " - ", b, " es: ", resta(a,b))
            case "3":
                a = input("Ingresa el primer numero: ")
                b = input("Ingrese el segundo numero: ")
                try:
                    a = int(a)
                    b = int(b)
                except ValueError:
                    print("los valores no son números")
                print("La multiplicación de ", a, " * ", b, " es: ", multiplicación(a,b))
            case "4":
                a = input("Ingresa el primer numero: ")
                b = input("Ingrese el segundo numero: ")
                try:
                    a = int(a)
                    b = int(b)
                except ValueError:
                    print("los valores no son números")
                print("La división de ", a, " / ", b, " es: ", division(a,b))
            case "5":
                a = input("Ingresa tu peso: ")
                try:
                    a = int(a)
                except ValueError:
                    print("los valores no son números")
                print(peso(a))
            case "6":
                q = False
                print("Gracias por usar la calculadora")