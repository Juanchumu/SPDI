# Modelado: 

Cuando la cantidad de imagenes para entrenamiento sea 
* multiplo de 10
se va a modelar.

Entonces, se sube
* a MiniO un modelo (esto se hace primero por que si hay un nuevo modelo DB y no esta el archivo va a explotar) 
* a la DB cual es el ultimo modelo 

# Notas: 

* Sabemos que esta mal.

Se va a modelar con pocos datos y con pocas epocas, pero esto es para poder probarlo en tiempo real y no esperar 2 o 5 horas hasta que salga el nuevo modelo.

Esto va a requerir torch, por lo que va a ser pesado. 


