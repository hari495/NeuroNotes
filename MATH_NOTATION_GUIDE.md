# Math Notation Guide

The frontend supports LaTeX/KaTeX rendering for mathematical expressions. This guide explains how to properly format math in the AI responses.

## Syntax

### Inline Math

Use single dollar signs `$...$` for inline math expressions:

```
The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.
```

**Renders as:** The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.

### Display Math (Block)

Use double dollar signs `$$...$$` for centered block equations:

```
$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$
```

**Renders as:** A centered, larger equation.

## Common Mathematical Notation

### Vectors

```
$\vec{v}$ or $\mathbf{v}$              → Vector
$\vec{e_1}, \vec{e_2}$                 → Vector basis
$\|\vec{v}\|$                          → Vector magnitude/norm
```

### Matrices

```
$$
A = \begin{bmatrix}
  a & b \\
  c & d
\end{bmatrix}
$$
```

Or inline: `$\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}$`

### Greek Letters

```
$\alpha, \beta, \gamma, \delta$       → α, β, γ, δ
$\theta, \phi, \psi, \omega$          → θ, φ, ψ, ω
$\Sigma, \Pi, \Omega$                 → Σ, Π, Ω
```

### Operators and Symbols

```
$\sum_{i=1}^{n} x_i$                  → Summation
$\prod_{i=1}^{n} x_i$                 → Product
$\int_a^b f(x) dx$                    → Integral
$\lim_{x \to \infty} f(x)$            → Limit
$\frac{\partial f}{\partial x}$       → Partial derivative
```

### Subscripts and Superscripts

```
$x_i$                                 → Subscript
$x^2$                                 → Superscript
$x_i^2$                               → Both
$x_{i,j}$                             → Multiple subscripts
```

### Sets and Logic

```
$\in, \notin, \subset, \subseteq$     → Set membership
$\cup, \cap, \emptyset$               → Set operations
$\forall, \exists, \nexists$          → Quantifiers
$\land, \lor, \neg$                   → Logical operators
```

### Relations

```
$\leq, \geq, \neq, \approx$           → Comparisons
$\equiv, \sim, \cong$                 → Equivalences
$\propto, \parallel, \perp$           → Proportional, parallel, perpendicular
```

## Common Patterns for Notes App

### Linear Algebra

```markdown
A **span** of vectors $\{\vec{v_1}, \vec{v_2}, ..., \vec{v_k}\}$ is the set of all linear combinations:

$$
\text{span}(\vec{v_1}, ..., \vec{v_k}) = \{c_1\vec{v_1} + c_2\vec{v_2} + ... + c_k\vec{v_k} : c_i \in \mathbb{R}\}
$$

For example, to check if $\vec{w}$ is in the span of $\vec{e_1}, \vec{e_2}$:

$$
\vec{w} = c_1\vec{e_1} + c_2\vec{e_2}
$$
```

### Calculus

```markdown
The derivative of $f(x) = x^2$ is:

$$
f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h} = 2x
$$
```

### Statistics

```markdown
The mean is $\mu = \frac{1}{n}\sum_{i=1}^{n} x_i$ and variance is:

$$
\sigma^2 = \frac{1}{n}\sum_{i=1}^{n} (x_i - \mu)^2
$$
```

### Algorithms

```markdown
Time complexity: $O(n \log n)$

Space complexity: $O(1)$
```

## Troubleshooting Weird Characters

If you see characters like `# »e1` or `# »v1` in PDFs, these should be converted to LaTeX:

| PDF Text | LaTeX | Rendered |
|----------|-------|----------|
| `# »e1` | `$\vec{e_1}$` | $\vec{e_1}$ |
| `# »v1` | `$\vec{v_1}$` | $\vec{v_1}$ |
| `R2` | `$\mathbb{R}^2$` | $\mathbb{R}^2$ |
| `R3` | `$\mathbb{R}^3$` | $\mathbb{R}^3$ |

## Tips for AI Responses

1. **Always use LaTeX for math**: Don't use ASCII approximations like `v1` or `e_1`, use `$\vec{v_1}$` or `$\vec{e_1}$`

2. **Use display math for important equations**: Makes them stand out and easier to read

3. **Combine with markdown**: You can mix math with other markdown features:
   ```markdown
   ## Theorem

   For any vectors $\vec{v_1}, \vec{v_2}$ in $\mathbb{R}^n$:

   $$
   \|\vec{v_1} + \vec{v_2}\| \leq \|\vec{v_1}\| + \|\vec{v_2}\|
   $$

   This is called the **triangle inequality**.
   ```

4. **Use proper formatting**: Add spaces around inline math for readability: `... is $x^2$ in the ...` not `...is$x^2$in...`

## Complete Example Response

```markdown
## Linear Independence

A set of vectors $\{\vec{v_1}, \vec{v_2}, ..., \vec{v_k}\}$ is **linearly independent** if the only solution to:

$$
c_1\vec{v_1} + c_2\vec{v_2} + ... + c_k\vec{v_k} = \vec{0}
$$

is $c_1 = c_2 = ... = c_k = 0$.

### Example

Are $\vec{e_1} = \begin{bmatrix} 1 \\ 0 \end{bmatrix}$ and $\vec{e_2} = \begin{bmatrix} 0 \\ 1 \end{bmatrix}$ linearly independent in $\mathbb{R}^2$?

**Solution**: We need to solve:

$$
c_1 \begin{bmatrix} 1 \\ 0 \end{bmatrix} + c_2 \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \end{bmatrix}
$$

This gives us:
- $c_1 = 0$
- $c_2 = 0$

Therefore, $\vec{e_1}$ and $\vec{e_2}$ are linearly independent.
```

## KaTeX Documentation

For a complete list of supported LaTeX commands, see:
https://katex.org/docs/supported.html
