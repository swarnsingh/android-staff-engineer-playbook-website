package dev.playbook.validation.fixtures.overloads
class OverloadContract {
 @JvmOverloads fun connect(a: Int = 1, required: String, b: Int = 2) = "$a:$required:$b"
}
