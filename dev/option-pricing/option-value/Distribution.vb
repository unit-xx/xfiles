Option Explicit On     'Requirs that all variables to be declared explicitly.
Option Compare Text 'Uppercase letters to be equivalent to lowercase letters.
'default first index of arrays.
Option Base 1       'The "Option Base" statment alowws to specify 0 or 1 as the

Module Distribution
    Global Const Pi = 3.14159265358979

    Public Function Max(ByVal X, ByVal y)
        Max = Application.Max(X, y)
    End Function

    Public Function Min(ByVal X, ByVal y)
        Min = Application.Min(X, y)
    End Function

    '// The normal distribution function
    Public Function ND(ByVal X As Double) As Double
        ND = 1 / Sqr(2 * Pi) * Exp(-X ^ 2 / 2)
    End Function


    '// The cumulative normal distribution function
    Public Function CND(ByVal X As Double) As Double

        Dim L As Double, K As Double
        Const a1 = 0.31938153 : Const a2 = -0.356563782 : Const a3 = 1.781477937
        Const a4 = -1.821255978 : Const a5 = 1.330274429

        L = Abs(X)
        K = 1 / (1 + 0.2316419 * L)
        CND = 1 - 1 / Sqr(2 * Pi) * Exp(-L ^ 2 / 2) * (a1 * K + a2 * K ^ 2 + a3 * K ^ 3 + a4 * K ^ 4 + a5 * K ^ 5)

        If X < 0 Then
            CND = 1 - CND
        End If
    End Function


    '// The cumulative bivariate normal distribution function
    Public Function CBND(ByVal a As Double, ByVal b As Double, ByVal rho As Double) As Double

        Dim X As Object, y As Object
        Dim rho1 As Double, rho2 As Double, delta As Double
        Dim a1 As Double, b1 As Double, Sum As Double
        Dim I As Integer, j As Integer

        X = Array(0.24840615, 0.39233107, 0.21141819, 0.03324666, 0.00082485334)
        y = Array(0.10024215, 0.48281397, 1.0609498, 1.7797294, 2.6697604)
        a1 = a / Sqr(2 * (1 - rho ^ 2))
        b1 = b / Sqr(2 * (1 - rho ^ 2))

        If a <= 0 And b <= 0 And rho <= 0 Then
            Sum = 0
            For I = 1 To 5
                For j = 1 To 5
                    Sum = Sum + X(I) * X(j) * Exp(a1 * (2 * y(I) - a1) _
                    + b1 * (2 * y(j) - b1) + 2 * rho * (y(I) - a1) * (y(j) - b1))
                Next
            Next
            CBND = Sqr(1 - rho ^ 2) / Pi * Sum
        ElseIf a <= 0 And b >= 0 And rho >= 0 Then
            CBND = CND(a) - CBND(a, -b, -rho)
        ElseIf a >= 0 And b <= 0 And rho >= 0 Then
            CBND = CND(b) - CBND(-a, b, -rho)
        ElseIf a >= 0 And b >= 0 And rho <= 0 Then
            CBND = CND(a) + CND(b) - 1 + CBND(-a, -b, rho)
        ElseIf a * b * rho > 0 Then
            rho1 = (rho * a - b) * Sgn(a) / Sqr(a ^ 2 - 2 * rho * a * b + b ^ 2)
            rho2 = (rho * b - a) * Sgn(b) / Sqr(a ^ 2 - 2 * rho * a * b + b ^ 2)
            delta = (1 - Sgn(a) * Sgn(b)) / 4
            CBND = CBND(a, 0, rho1) + CBND(b, 0, rho2) - delta
        End If
    End Function
End Module
