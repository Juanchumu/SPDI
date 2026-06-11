# Prediccion:

Se toma una de la DB una orden Lista para predecir
* Se pide a MiniO los archivos para la prediccion 
* Se manda a MiniO la prediccion
* Se manda a la DB cambios de estados de la orden
* Se añade tambien que modelo fue utilizado para la prediccion

# Notas: 

Esto va a requerir torch, por lo que va a ser pesado.

Va a seguir el metodo de utilizar el ultimo modelo disponible
debido a que es un sistema de tiempo real. 
