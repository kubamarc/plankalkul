# About
This Plankalkül interpreter is going to be a part of my BSc thesis.
It is not interpreting Plankalkül in its original form, because of its strange two-dimensional syntax,
but a flattened, plaintext version of the language, with a few additional modifications.

# Flow
The flow of this program is quite simple.
The file `plankalkul.py` is the core of program. It takes a file with Plankalkül code as an argument, and gives it to the `tokenizer` module to tokenize it.
After tokenization, we parse the code using the `parser` module, then typecheck it in `typechecker`, and execute it using the `run` module.

# Examples
In the `examples` directory there are a few example programs written in my version of Plankalkül.
`fib.pla` and `fib2.pla` calculate Fibbonacci numbers using two methods: iterative and recursive, respectively.
`even.pla` checks if a number is even using mutually recursive plans.
`program19.pla` shows how to parametrise plans with type-variables.
