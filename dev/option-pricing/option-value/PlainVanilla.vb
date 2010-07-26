Option Explicit On     'Requires that all variables to be declared explicitly.
Option Compare Text 'Uppercase letters to be equivalent to lowercase letters.
Imports System.Math

Module PlainVanilla


    '// * European options *

    '// Black and Scholes (1973) Stock options
    Public Function BlackScholes(ByVal CallPutFlag As String, ByVal S As Double, ByVal X _
                    As Double, ByVal T As Double, ByVal r As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (r + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        If CallPutFlag = "c" Then
            BlackScholes = S * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            BlackScholes = X * Exp(-r * T) * CND(-d2) - S * CND(-d1)
        End If
    End Function


    '// Merton (1973) Options on stock indices
    Public Function Merton73(ByVal CallPutFlag As String, ByVal S As Double, ByVal X _
                    As Double, ByVal T As Double, ByVal r As Double, ByVal q As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (r - q + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        If CallPutFlag = "c" Then
            Merton73 = S * Exp(-q * T) * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            Merton73 = X * Exp(-r * T) * CND(-d2) - S * Exp(-q * T) * CND(-d1)
        End If
    End Function


    '// Black (1977) Options on futures/forwards
    Public Function Black76(ByVal CallPutFlag As String, ByVal F As Double, ByVal X _
                    As Double, ByVal T As Double, ByVal r As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(F / X) + (v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        If CallPutFlag = "c" Then
            Black76 = Exp(-r * T) * (F * CND(d1) - X * CND(d2))
        ElseIf CallPutFlag = "p" Then
            Black76 = Exp(-r * T) * (X * CND(-d2) - F * CND(-d1))
        End If
    End Function


    '// Garman and Kohlhagen (1983) Currency options
    Public Function GarmanKolhagen(ByVal CallPutFlag As String, ByVal S As Double, ByVal X _
                    As Double, ByVal T As Double, ByVal r As Double, ByVal rf As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (r - rf + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        If CallPutFlag = "c" Then
            GarmanKolhagen = S * Exp(-rf * T) * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            GarmanKolhagen = X * Exp(-r * T) * CND(-d2) - S * Exp(-rf * T) * CND(-d1)
        End If
    End Function


    '// The generalized Black and Scholes formula
    Public Function GBlackScholes(ByVal CallPutFlag As String, ByVal S As Double, ByVal X _
                    As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        If CallPutFlag = "c" Then
            GBlackScholes = S * Exp((b - r) * T) * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            GBlackScholes = X * Exp(-r * T) * CND(-d2) - S * Exp((b - r) * T) * CND(-d1)
        End If
    End Function


    '// Delta for the generalized Black and Scholes formula
    Public Function GDelta(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, _
                    ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))

        If CallPutFlag = "c" Then
            GDelta = Exp((b - r) * T) * CND(d1)
        ElseIf CallPutFlag = "p" Then
            GDelta = Exp((b - r) * T) * (CND(d1) - 1)
        End If
    End Function


    '// Gamma for the generalized Black and Scholes formula
    Public Function GGamma(ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        GGamma = Exp((b - r) * T) * ND(d1) / (S * v * Sqrt(T))
    End Function


    '// Theta for the generalized Black and Scholes formula
    Public Function GTheta(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        If CallPutFlag = "c" Then
            GTheta = -S * Exp((b - r) * T) * ND(d1) * v / (2 * Sqrt(T)) - (b - r) * S * Exp((b - r) * T) * CND(d1) - r * X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            GTheta = -S * Exp((b - r) * T) * ND(d1) * v / (2 * Sqrt(T)) + (b - r) * S * Exp((b - r) * T) * CND(-d1) + r * X * Exp(-r * T) * CND(-d2)
        End If
    End Function


    '// Vega for the generalized Black and Scholes formula
    Public Function GVega(ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        GVega = S * Exp((b - r) * T) * ND(d1) * Sqrt(T)
    End Function


    '// Rho for the generalized Black and Scholes formula
    Public Function GRho(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        If CallPutFlag = "c" Then
            If b <> 0 Then
                GRho = T * X * Exp(-r * T) * CND(d2)
            Else
                GRho = -T * GBlackScholes(CallPutFlag, S, X, T, r, b, v)
            End If
        ElseIf CallPutFlag = "p" Then
            If b <> 0 Then
                GRho = -T * X * Exp(-r * T) * CND(-d2)
            Else
                GRho = -T * GBlackScholes(CallPutFlag, S, X, T, r, b, v)
            End If
        End If
    End Function

    '// Carry for the generalized Black and Scholes formula
    Public Function GCarry(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        If CallPutFlag = "c" Then
            GCarry = T * S * Exp((b - r) * T) * CND(d1)
        ElseIf CallPutFlag = "p" Then
            GCarry = -T * S * Exp((b - r) * T) * CND(-d1)
        End If
    End Function


    '// French (1984) adjusted Black and Scholes model for trading day volatility
    Public Function French(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal t1 As Double, _
                    ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + b * T + v ^ 2 / 2 * t1) / (v * Sqrt(t1))
        d2 = d1 - v * Sqrt(t1)

        If CallPutFlag = "c" Then
            French = S * Exp((b - r) * T) * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            French = X * Exp(-r * T) * CND(-d2) - S * Exp((b - r) * T) * CND(-d1)
        End If
    End Function


    '// Merton (1976) jump diffusion model
    Public Function JumpDiffusion(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal v As Double, _
                    ByVal lambda As Double, ByVal gamma As Double) As Double

        Dim delta As Double, Sum As Double
        Dim Z As Double, vi As Double
        Dim I As Integer

        delta = Sqrt(gamma * v ^ 2 / lambda)
        Z = Sqrt(v ^ 2 - lambda * delta ^ 2)
        Sum = 0
        For I = 0 To 10
            vi = Sqrt(Z ^ 2 + delta ^ 2 * (I / T))
            Sum = Sum + Exp(-lambda * T) * (lambda * T) ^ I / factorial(I) * _
            GBlackScholes(CallPutFlag, S, X, T, r, r, vi)
        Next
        JumpDiffusion = Sum
    End Function


    '// Miltersen Schwartz (1997) commodity option model
    Public Function MiltersenSwartz(ByVal CallPutFlag As String, ByVal Pt As Double, ByVal FT As Double, ByVal X As Double, ByVal t1 As Double, _
                    ByVal T2 As Double, ByVal vS As Double, ByVal vE As Double, ByVal vf As Double, ByVal rhoSe As Double, _
                    ByVal rhoSf As Double, ByVal rhoef As Double, ByVal Kappae As Double, ByVal Kappaf As Double) As Double

        Dim vz As Double, vxz As Double
        Dim d1 As Double, d2 As Double

        vz = vS ^ 2 * t1 + 2 * vS * (vf * rhoSf * 1 / Kappaf * (t1 - 1 / Kappaf * Exp(-Kappaf * T2) * (Exp(Kappaf * t1) - 1)) _
            - vE * rhoSe * 1 / Kappae * (t1 - 1 / Kappae * Exp(-Kappae * T2) * (Exp(Kappae * t1) - 1))) _
            + vE ^ 2 * 1 / Kappae ^ 2 * (t1 + 1 / (2 * Kappae) * Exp(-2 * Kappae * T2) * (Exp(2 * Kappae * t1) - 1) - 2 * 1 / Kappae * Exp(-Kappae * T2) * (Exp(Kappae * t1) - 1)) _
            + vf ^ 2 * 1 / Kappaf ^ 2 * (t1 + 1 / (2 * Kappaf) * Exp(-2 * Kappaf * T2) * (Exp(2 * Kappaf * t1) - 1) - 2 * 1 / Kappaf * Exp(-Kappaf * T2) * (Exp(Kappaf * t1) - 1)) _
            - 2 * vE * vf * rhoef * 1 / Kappae * 1 / Kappaf * (t1 - 1 / Kappae * Exp(-Kappae * T2) * (Exp(Kappae * t1) - 1) - 1 / Kappaf * Exp(-Kappaf * T2) * (Exp(Kappaf * t1) - 1) _
            + 1 / (Kappae + Kappaf) * Exp(-(Kappae + Kappaf) * T2) * (Exp((Kappae + Kappaf) * t1) - 1))

        vxz = vf * 1 / Kappaf * (vS * rhoSf * (t1 - 1 / Kappaf * (1 - Exp(-Kappaf * t1))) _
            + vf * 1 / Kappaf * (t1 - 1 / Kappaf * Exp(-Kappaf * T2) * (Exp(Kappaf * t1) - 1) - 1 / Kappaf * (1 - Exp(-Kappaf * t1)) _
            + 1 / (2 * Kappaf) * Exp(-Kappaf * T2) * (Exp(Kappaf * t1) - Exp(-Kappaf * t1))) _
            - vE * rhoef * 1 / Kappae * (t1 - 1 / Kappae * Exp(-Kappae * T2) * (Exp(Kappae * t1) - 1) - 1 / Kappaf * (1 - Exp(-Kappaf * t1)) _
            + 1 / (Kappae + Kappaf) * Exp(-Kappae * T2) * (Exp(Kappae * t1) - Exp(-Kappaf * t1))))

        vz = Sqrt(vz)

        d1 = (Log(FT / X) - vxz + vz ^ 2 / 2) / vz
        d2 = (Log(FT / X) - vxz - vz ^ 2 / 2) / vz

        If CallPutFlag = "c" Then
            MiltersenSwartz = Pt * (FT * Exp(-vxz) * CND(d1) - X * CND(d2))
        ElseIf CallPutFlag = "p" Then
            MiltersenSwartz = Pt * (X * CND(-d2) - FT * Exp(-vxz) * CND(-d1))
        End If

    End Function


    '// * American options *


    '// American Calls on stocks with known dividends, Roll-Geske-Whaley
    Public Function RollGeskeWhaley(ByVal S As Double, ByVal X As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal r As Double, ByVal d As Double, ByVal v As Double) As Double
        't1 time to dividend payout
        'T2 time to option expiration

        Dim Sx As Double, I As Double
        Dim a1 As Double, a2 As Double, b1 As Double, b2 As Double
        Dim HighS As Double, LowS As Double, epsilon As Double
        Dim ci As Double, infinity As Double

        infinity = 100000000
        epsilon = 0.00001
        Sx = S - d * Exp(-r * t1)
        If d <= X * (1 - Exp(-r * (T2 - t1))) Then '// Not optimal to exercise
            RollGeskeWhaley = BlackScholes("c", Sx, X, T2, r, v)
            Exit Function
        End If
        ci = BlackScholes("c", S, X, T2 - t1, r, v)
        HighS = S
        While (ci - HighS - d + X) > 0 And HighS < infinity
            HighS = HighS * 2
            ci = BlackScholes("c", HighS, X, T2 - t1, r, v)
        End While
        If HighS > infinity Then
            RollGeskeWhaley = BlackScholes("c", Sx, X, T2, r, v)
            Exit Function
        End If

        LowS = 0
        I = HighS * 0.5
        ci = BlackScholes("c", I, X, T2 - t1, r, v)

        '// Search algorithm to find the critical stock price I
        While Abs(ci - I - d + X) > epsilon And HighS - LowS > epsilon
            If (ci - I - d + X) < 0 Then
                HighS = I
            Else
                LowS = I
            End If
            I = (HighS + LowS) / 2
            ci = BlackScholes("c", I, X, T2 - t1, r, v)
        End While
        a1 = (Log(Sx / X) + (r + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        a2 = a1 - v * Sqrt(T2)
        b1 = (Log(Sx / I) + (r + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        b2 = b1 - v * Sqrt(t1)

        RollGeskeWhaley = Sx * CND(b1) + Sx * CBND(a1, -b1, -Sqrt(t1 / T2)) - X * Exp(-r * T2) * CBND(a2, -b2, -Sqrt(t1 / T2)) - (X - d) * Exp(-r * t1) * CND(b2)
    End Function


    '// The Barone-Adesi and Whaley (1987) American approximation
    Public Function BAWAmericanApprox(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double
        If CallPutFlag = "c" Then
            BAWAmericanApprox = BAWAmericanCallApprox(S, X, T, r, b, v)
        ElseIf CallPutFlag = "p" Then
            BAWAmericanApprox = BAWAmericanPutApprox(S, X, T, r, b, v)
        End If
    End Function

    '// American call
    Private Function BAWAmericanCallApprox(ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim Sk As Double, n As Double, K As Double
        Dim d1 As Double, Q2 As Double, a2 As Double

        If b >= r Then
            BAWAmericanCallApprox = GBlackScholes("c", S, X, T, r, b, v)
        Else
            Sk = Kc(X, T, r, b, v)
            n = 2 * b / v ^ 2                                           '
            K = 2 * r / (v ^ 2 * (1 - Exp(-r * T)))
            d1 = (Log(Sk / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
            Q2 = (-(n - 1) + Sqrt((n - 1) ^ 2 + 4 * K)) / 2
            a2 = (Sk / Q2) * (1 - Exp((b - r) * T) * CND(d1))
            If S < Sk Then
                BAWAmericanCallApprox = GBlackScholes("c", S, X, T, r, b, v) + a2 * (S / Sk) ^ Q2
            Else
                BAWAmericanCallApprox = S - X
            End If
        End If
    End Function

    '// Newton Raphson algorithm to solve for the critical commodity price for a Call
    Private Function Kc(ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim n As Double, m As Double
        Dim Su As Double, Si As Double
        Dim h2 As Double, K As Double
        Dim d1 As Double, Q2 As Double, q2u As Double
        Dim LHS As Double, RHS As Double
        Dim bi As Double, E As Double

        '// Calculation of seed value, Si
        n = 2 * b / v ^ 2
        m = 2 * r / v ^ 2
        q2u = (-(n - 1) + Sqrt((n - 1) ^ 2 + 4 * m)) / 2
        Su = X / (1 - 1 / q2u)
        h2 = -(b * T + 2 * v * Sqrt(T)) * X / (Su - X)
        Si = X + (Su - X) * (1 - Exp(h2))

        K = 2 * r / (v ^ 2 * (1 - Exp(-r * T)))
        d1 = (Log(Si / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        Q2 = (-(n - 1) + Sqrt((n - 1) ^ 2 + 4 * K)) / 2
        LHS = Si - X
        RHS = GBlackScholes("c", Si, X, T, r, b, v) + (1 - Exp((b - r) * T) * CND(d1)) * Si / Q2
        bi = Exp((b - r) * T) * CND(d1) * (1 - 1 / Q2) + (1 - Exp((b - r) * T) * CND(d1) / (v * Sqrt(T))) / Q2
        E = 0.000001
        '// Newton Raphson algorithm for finding critical price Si
        While Abs(LHS - RHS) / X > E
            Si = (X + RHS - bi * Si) / (1 - bi)
            d1 = (Log(Si / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
            LHS = Si - X
            RHS = GBlackScholes("c", Si, X, T, r, b, v) + (1 - Exp((b - r) * T) * CND(d1)) * Si / Q2
            bi = Exp((b - r) * T) * CND(d1) * (1 - 1 / Q2) + (1 - Exp((b - r) * T) * ND(d1) / (v * Sqrt(T))) / Q2
        End While
        Kc = Si
    End Function
    '// American put
    Private Function BAWAmericanPutApprox(ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim Sk As Double, n As Double, K As Double
        Dim d1 As Double, Q1 As Double, a1 As Double

        Sk = Kp(X, T, r, b, v)
        n = 2 * b / v ^ 2
        K = 2 * r / (v ^ 2 * (1 - Exp(-r * T)))
        d1 = (Log(Sk / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        Q1 = (-(n - 1) - Sqrt((n - 1) ^ 2 + 4 * K)) / 2
        a1 = -(Sk / Q1) * (1 - Exp((b - r) * T) * CND(-d1))

        If S > Sk Then
            BAWAmericanPutApprox = GBlackScholes("p", S, X, T, r, b, v) + a1 * (S / Sk) ^ Q1
        Else
            BAWAmericanPutApprox = X - S
        End If
    End Function

    '// Newton Raphson algorithm to solve for the critical commodity price for a Put
    Private Function Kp(ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double


        Dim n As Double, m As Double
        Dim Su As Double, Si As Double
        Dim h1 As Double, K As Double
        Dim d1 As Double, q1u As Double, Q1 As Double
        Dim LHS As Double, RHS As Double
        Dim bi As Double, E As Double

        '// Calculation of seed value, Si
        n = 2 * b / v ^ 2
        m = 2 * r / v ^ 2
        q1u = (-(n - 1) - Sqrt((n - 1) ^ 2 + 4 * m)) / 2
        Su = X / (1 - 1 / q1u)
        h1 = (b * T - 2 * v * Sqrt(T)) * X / (X - Su)
        Si = Su + (X - Su) * Exp(h1)


        K = 2 * r / (v ^ 2 * (1 - Exp(-r * T)))
        d1 = (Log(Si / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        Q1 = (-(n - 1) - Sqrt((n - 1) ^ 2 + 4 * K)) / 2
        LHS = X - Si
        RHS = GBlackScholes("p", Si, X, T, r, b, v) - (1 - Exp((b - r) * T) * CND(-d1)) * Si / Q1
        bi = -Exp((b - r) * T) * CND(-d1) * (1 - 1 / Q1) - (1 + Exp((b - r) * T) * ND(-d1) / (v * Sqrt(T))) / Q1
        E = 0.000001
        '// Newton Raphson algorithm for finding critical price Si
        While Abs(LHS - RHS) / X > E
            Si = (X - RHS + bi * Si) / (1 + bi)
            d1 = (Log(Si / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
            LHS = X - Si
            RHS = GBlackScholes("p", Si, X, T, r, b, v) - (1 - Exp((b - r) * T) * CND(-d1)) * Si / Q1
            bi = -Exp((b - r) * T) * CND(-d1) * (1 - 1 / Q1) - (1 + Exp((b - r) * T) * CND(-d1) / (v * Sqrt(T))) / Q1
        End While
        Kp = Si
    End Function


    '// The Bjerksund and Stensland (1993) American approximation
    Public Function BSAmericanApprox(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double
        If CallPutFlag = "c" Then
            BSAmericanApprox = BSAmericanCallApprox(S, X, T, r, b, v)
        ElseIf CallPutFlag = "p" Then  '// Use the Bjerksund and Stensland put-call transformation
            BSAmericanApprox = BSAmericanCallApprox(X, S, T, r - b, -b, v)
        End If
    End Function

    Public Function BSAmericanCallApprox(ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim BInfinity As Double, B0 As Double
        Dim ht As Double, I As Double
        Dim alpha As Double, Beta As Double

        If b >= r Then '// Never optimal to exersice before maturity
            BSAmericanCallApprox = GBlackScholes("c", S, X, T, r, b, v)
        Else
            Beta = (1 / 2 - b / v ^ 2) + Sqrt((b / v ^ 2 - 1 / 2) ^ 2 + 2 * r / v ^ 2)
            BInfinity = Beta / (Beta - 1) * X
            B0 = Max(X, r / (r - b) * X)
            ht = -(b * T + 2 * v * Sqrt(T)) * B0 / (BInfinity - B0)
            I = B0 + (BInfinity - B0) * (1 - Exp(ht))
            alpha = (I - X) * I ^ (-Beta)
            If S >= I Then
                BSAmericanCallApprox = S - X
            Else
                BSAmericanCallApprox = alpha * S ^ Beta - alpha * phi(S, T, Beta, I, I, r, b, v) + phi(S, T, 1, I, I, r, b, v) - phi(S, T, 1, X, I, r, b, v) - X * phi(S, T, 0, I, I, r, b, v) + X * phi(S, T, 0, X, I, r, b, v)
            End If
        End If
    End Function

    Private Function phi(ByVal S As Double, ByVal T As Double, ByVal gamma As Double, ByVal H As Double, ByVal I As Double, _
            ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim lambda As Double, kappa As Double
        Dim d As Double

        lambda = (-r + gamma * b + 0.5 * gamma * (gamma - 1) * v ^ 2) * T
        d = -(Log(S / H) + (b + (gamma - 0.5) * v ^ 2) * T) / (v * Sqrt(T))
        kappa = 2 * b / (v ^ 2) + (2 * gamma - 1)
        phi = Exp(lambda) * S ^ gamma * (CND(d) - (I / S) ^ kappa * CND(d - 2 * Log(I / S) / (v * Sqrt(T))))
    End Function
End Module
