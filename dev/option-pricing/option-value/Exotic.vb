Option Explicit On     'Requires that all variables to be declared explicitly.
Option Compare Text 'Uppercase letters to be equivalent to lowercase letters.
Imports System.Math

Module Exotic
    '// Executive stock options
    Public Function Executive(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double, ByVal lambda As Double) As Double

        Executive = Math.Exp(-lambda * T) * GBlackScholes(CallPutFlag, S, X, T, r, b, v)

    End Function


    '// Forward start options
    Public Function ForwardStartOption(ByVal CallPutFlag As String, ByVal S As Double, ByVal alpha As Double, ByVal t1 As Double, _
                    ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        ForwardStartOption = S * Math.Exp((b - r) * t1) * GBlackScholes(CallPutFlag, 1, alpha, T - t1, r, b, v)

    End Function


    '// Time switch options (discrete)
    Public Function TimeSwitchOption(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal a As Double, ByVal T As Double, ByVal m As Integer, ByVal dt As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim Sum As Double, d As Double
        Dim I As Integer, n As Integer, Z As Integer

        n = T / dt
        Sum = 0
        If CallPutFlag = "c" Then
            Z = 1
        ElseIf CallPutFlag = "p" Then
            Z = -1
        End If
        For I = 1 To n
            d = (Math.Log(S / X) + (b - v ^ 2 / 2) * I * dt) / (v * Math.Sqrt(I * dt))
            Sum = Sum + CND(Z * d) * dt
        Next
        TimeSwitchOption = a * Math.Exp(-r * T) * Sum + dt * a * Math.Exp(-r * T) * m
    End Function


    '// Simple chooser options
    Public Function SimpleChooser(ByVal S As Double, ByVal X As Double, ByVal t1 As Double, ByVal T2 As Double, _
                    ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d As Double, y As Double

        d = (Math.Log(S / X) + (b + v ^ 2 / 2) * T2) / (v * Math.Sqrt(T2))
        y = (Math.Log(S / X) + b * T2 + v ^ 2 * t1 / 2) / (v * Math.Sqrt(t1))

        SimpleChooser = S * Math.Exp((b - r) * T2) * CND(d) - X * Math.Exp(-r * T2) * CND(d - v * Math.Sqrt(T2)) _
        - S * Math.Exp((b - r) * T2) * CND(-y) + X * Math.Exp(-r * T2) * CND(-y + v * Math.Sqrt(t1))
    End Function


    '// Complex chooser options
    Public Function ComplexChooser(ByVal S As Double, ByVal Xc As Double, ByVal Xp As Double, ByVal T As Double, ByVal Tc As Double, _
                    ByVal Tp As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double, y1 As Double, y2 As Double
        Dim rho1 As Double, rho2 As Double, I As Double

        I = CriticalValueChooser(S, Xc, Xp, T, Tc, Tp, r, b, v)
        d1 = (Math.Log(S / I) + (b + v ^ 2 / 2) * T) / (v * Math.Sqrt(T))
        d2 = d1 - v * Math.Sqrt(T)
        y1 = (Math.Log(S / Xc) + (b + v ^ 2 / 2) * Tc) / (v * Math.Sqrt(Tc))
        y2 = (Math.Log(S / Xp) + (b + v ^ 2 / 2) * Tp) / (v * Math.Sqrt(Tp))
        rho1 = Math.Sqrt(T / Tc)
        rho2 = Math.Sqrt(T / Tp)

        ComplexChooser = S * Math.Exp((b - r) * Tc) * CBND(d1, y1, rho1) - Xc * Math.Exp(-r * Tc) * CBND(d2, y1 - v * Math.Sqrt(Tc), rho1) - S * Exp((b - r) * Tp) * CBND(-d1, -y2, rho2) + Xp * Exp(-r * Tp) * CBND(-d2, -y2 + v * Sqrt(Tp), rho2)
    End Function
    '// Critical value complex chooser option
    Private Function CriticalValueChooser(ByVal S As Double, ByVal Xc As Double, ByVal Xp As Double, ByVal T As Double, _
                    ByVal Tc As Double, ByVal Tp As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim Sv As Double, ci As Double, Pi As Double, epsilon As Double
        Dim dc As Double, dp As Double, yi As Double, di As Double

        Sv = S

        ci = GBlackScholes("c", Sv, Xc, Tc - T, r, b, v)
        Pi = GBlackScholes("p", Sv, Xp, Tp - T, r, b, v)
        dc = GDelta("c", Sv, Xc, Tc - T, r, b, v)
        dp = GDelta("p", Sv, Xp, Tp - T, r, b, v)
        yi = ci - Pi
        di = dc - dp
        epsilon = 0.001
        'Newton-Raphson s縦eprosess
        While Abs(yi) > epsilon
            Sv = Sv - (yi) / di
            ci = GBlackScholes("c", Sv, Xc, Tc - T, r, b, v)
            Pi = GBlackScholes("p", Sv, Xp, Tp - T, r, b, v)
            dc = GDelta("c", Sv, Xc, Tc - T, r, b, v)
            dp = GDelta("p", Sv, Xp, Tp - T, r, b, v)
            yi = ci - Pi
            di = dc - dp
        End While
        CriticalValueChooser = Sv
    End Function


    '// Options on options
    Public Function OptionsOnOptions(ByVal TypeFlag As String, ByVal S As Double, ByVal X1 As Double, ByVal X2 As Double, ByVal t1 As Double, _
                    ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim y1 As Double, y2 As Double, z1 As Double, z2 As Double
        Dim I As Double, rho As Double, CallPutFlag As String

        If TypeFlag = "cc" Or TypeFlag = "pc" Then
            CallPutFlag = "c"
        Else
            CallPutFlag = "p"
        End If

        I = CriticalValueOptionsOnOptions(CallPutFlag, X1, X2, T2 - t1, r, b, v)

        rho = Sqrt(t1 / T2)
        y1 = (Log(S / I) + (b + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        y2 = y1 - v * Sqrt(t1)
        z1 = (Log(S / X1) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        z2 = z1 - v * Sqrt(T2)

        If TypeFlag = "cc" Then
            OptionsOnOptions = S * Exp((b - r) * T2) * CBND(z1, y1, rho) - X1 * Exp(-r * T2) * CBND(z2, y2, rho) - X2 * Exp(-r * t1) * CND(y2)
        ElseIf TypeFlag = "pc" Then
            OptionsOnOptions = X1 * Exp(-r * T2) * CBND(z2, -y2, -rho) - S * Exp((b - r) * T2) * CBND(z1, -y1, -rho) + X2 * Exp(-r * t1) * CND(-y2)
        ElseIf TypeFlag = "cp" Then
            OptionsOnOptions = X1 * Exp(-r * T2) * CBND(-z2, -y2, rho) - S * Exp((b - r) * T2) * CBND(-z1, -y1, rho) - X2 * Exp(-r * t1) * CND(-y2)
        ElseIf TypeFlag = "pp" Then
            OptionsOnOptions = S * Exp((b - r) * T2) * CBND(-z1, y1, -rho) - X1 * Exp(-r * T2) * CBND(-z2, y2, -rho) + Exp(-r * t1) * X2 * CND(y2)
        End If
    End Function
    '// Calculation of critical price options on options
    Private Function CriticalValueOptionsOnOptions(ByVal CallPutFlag As String, ByVal X1 As Double, ByVal X2 As Double, ByVal T As Double, _
                    ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim Si As Double, ci As Double, di As Double, epsilon As Double

        Si = X1
        ci = GBlackScholes(CallPutFlag, Si, X1, T, r, b, v)
        di = GDelta(CallPutFlag, Si, X1, T, r, b, v)
        epsilon = 0.000001
        '// Newton-Raphson algorithm
        While Abs(ci - X2) > epsilon
            Si = Si - (ci - X2) / di
            ci = GBlackScholes(CallPutFlag, Si, X1, T, r, b, v)
            di = GDelta(CallPutFlag, Si, X1, T, r, b, v)
        End While
        CriticalValueOptionsOnOptions = Si
    End Function


    '// Writer extendible options
    Public Function ExtendibleWriter(ByVal CallPutFlag As String, ByVal S As Double, ByVal X1 As Double, ByVal X2 As Double, ByVal t1 As Double, _
                    ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim rho As Double, z1 As Double, z2 As Double
        rho = Sqrt(t1 / T2)
        z1 = (Log(S / X2) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        z2 = (Log(S / X1) + (b + v ^ 2 / 2) * t1) / (v * Sqrt(t1))

        If CallPutFlag = "c" Then
            ExtendibleWriter = GBlackScholes(CallPutFlag, S, X1, t1, r, b, v) + S * Exp((b - r) * T2) * CBND(z1, -z2, -rho) - X2 * Exp(-r * T2) * CBND(z1 - Sqrt(v ^ 2 * T2), -z2 + Sqrt(v ^ 2 * t1), -rho)
        ElseIf CallPutFlag = "p" Then
            ExtendibleWriter = GBlackScholes(CallPutFlag, S, X1, t1, r, b, v) + X2 * Exp(-r * T2) * CBND(-z1 + Sqrt(v ^ 2 * T2), z2 - Sqrt(v ^ 2 * t1), -rho) - S * Exp((b - r) * T2) * CBND(-z1, z2, -rho)
        End If
    End Function


    '// Two asset correlation options
    Public Function TwoAssetCorrelation(ByVal CallPutFlag As String, ByVal S1 As Double, ByVal S2 As Double, ByVal X1 As Double, ByVal X2 As Double, ByVal T As Double, _
                    ByVal b1 As Double, ByVal b2 As Double, ByVal r As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double)

        Dim y1 As Double, y2 As Double

        y1 = (Log(S1 / X1) + (b1 - v1 ^ 2 / 2) * T) / (v1 * Sqrt(T))
        y2 = (Log(S2 / X2) + (b2 - v2 ^ 2 / 2) * T) / (v2 * Sqrt(T))

        If CallPutFlag = "c" Then
            TwoAssetCorrelation = S2 * Exp((b2 - r) * T) * CBND(y2 + v2 * Sqrt(T), y1 + rho * v2 * Sqrt(T), rho) _
            - X2 * Exp(-r * T) * CBND(y2, y1, rho)
        ElseIf CallPutFlag = "p" Then
            TwoAssetCorrelation = X2 * Exp(-r * T) * CBND(-y2, -y1, rho) _
            - S2 * Exp((b2 - r) * T) * CBND(-y2 - v2 * Sqrt(T), -y1 - rho * v2 * Sqrt(T), rho)
        End If
    End Function


    '// European option to exchange one asset for another
    Public Function EuropeanExchangeOption(ByVal S1 As Double, ByVal S2 As Double, ByVal Q1 As Double, ByVal Q2 As Double, ByVal T As Double, ByVal r As Double, ByVal b1 As Double, _
                    ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim v As Double, d1 As Double, d2 As Double

        v = Sqrt(v1 ^ 2 + v2 ^ 2 - 2 * rho * v1 * v2)
        d1 = (Log(Q1 * S1 / (Q2 * S2)) + (b1 - b2 + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        EuropeanExchangeOption = Q1 * S1 * Exp((b1 - r) * T) * CND(d1) - Q2 * S2 * Exp((b2 - r) * T) * CND(d2)
    End Function


    '// American option to exchange one asset for another
    Public Function AmericanExchangeOption(ByVal S1 As Double, ByVal S2 As Double, ByVal Q1 As Double, ByVal Q2 As Double, ByVal T As Double, _
                ByVal r As Double, ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double
        Dim v As Double
        v = Sqrt(v1 ^ 2 + v2 ^ 2 - 2 * rho * v1 * v2)
        AmericanExchangeOption = BSAmericanApprox("c", Q1 * S1, Q2 * S2, T, r - b2, b1 - b2, v)
    End Function


    '// Exchange options on exchange options
    Public Function ExchangeExchangeOption(ByVal TypeFlag As Integer, ByVal S1 As Double, ByVal S2 As Double, ByVal q As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal r As Double, ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim I As Double, I1 As Double
        Dim d1 As Double, d2 As Double
        Dim d3 As Double, d4 As Double
        Dim y1 As Double, y2 As Double
        Dim y3 As Double, y4 As Double
        Dim v As Double, id As Integer

        v = Sqrt(v1 ^ 2 + v2 ^ 2 - 2 * rho * v1 * v2)
        I1 = S1 * Exp((b1 - r) * (T2 - t1)) / (S2 * Exp((b2 - r) * (T2 - t1)))

        If TypeFlag = 1 Or TypeFlag = 2 Then
            id = 1
        Else
            id = 2
        End If

        I = CriticalPrice(id, I1, t1, T2, v, q)
        d1 = (Log(S1 / (I * S2)) + (b1 - b2 + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        d2 = d1 - v * Sqrt(t1)
        d3 = (Log((I * S2) / S1) + (b2 - b1 + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        d4 = d3 - v * Sqrt(t1)
        y1 = (Log(S1 / S2) + (b1 - b2 + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        y2 = y1 - v * Sqrt(T2)
        y3 = (Log(S2 / S1) + (b2 - b1 + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        y4 = y3 - v * Sqrt(T2)

        If TypeFlag = 1 Then
            ExchangeExchangeOption = -S2 * Exp((b2 - r) * T2) * CBND(d2, y2, Sqrt(t1 / T2)) + S1 * Exp((b1 - r) * T2) * CBND(d1, y1, Sqrt(t1 / T2)) - q * S2 * Exp((b2 - r) * t1) * CND(d2)
        ElseIf TypeFlag = 2 Then
            ExchangeExchangeOption = S2 * Exp((b2 - r) * T2) * CBND(d3, y2, -Sqrt(t1 / T2)) - S1 * Exp((b1 - r) * T2) * CBND(d4, y1, -Sqrt(t1 / T2)) + q * S2 * Exp((b2 - r) * t1) * CND(d3)
        ElseIf TypeFlag = 3 Then
            ExchangeExchangeOption = S2 * Exp((b2 - r) * T2) * CBND(d3, y3, Sqrt(t1 / T2)) - S1 * Exp((b1 - r) * T2) * CBND(d4, y4, Sqrt(t1 / T2)) - q * S2 * Exp((b2 - r) * t1) * CND(d3)
        ElseIf TypeFlag = 4 Then
            ExchangeExchangeOption = -S2 * Exp((b2 - r) * T2) * CBND(d2, y3, -Sqrt(t1 / T2)) + S1 * Exp((b1 - r) * T2) * CBND(d1, y4, -Sqrt(t1 / T2)) + q * S2 * Exp((b2 - r) * t1) * CND(d2)
        End If
    End Function
    '// Numerical search algorithm to find critical price I
    Private Function CriticalPrice(ByVal id As Integer, ByVal I1 As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal v As Double, ByVal q As Double) As Double
        Dim Ii As Double, yi As Double, di As Double
        Dim epsilon As Double

        Ii = I1
        yi = CriticalPart3(id, Ii, t1, T2, v)
        di = CriticalPart2(id, Ii, t1, T2, v)
        epsilon = 0.00001
        While Abs(yi - q) > epsilon
            Ii = Ii - (yi - q) / di
            yi = CriticalPart3(id, Ii, t1, T2, v)
            di = CriticalPart2(id, Ii, t1, T2, v)
        End While
        CriticalPrice = Ii
    End Function
    Private Function CriticalPart2(ByVal id As Integer, ByVal I As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal v As Double) As Double
        Dim z1 As Double, z2 As Double
        If id = 1 Then
            z1 = (Log(I) + v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            CriticalPart2 = CND(z1)
        ElseIf id = 2 Then
            z2 = (-Log(I) - v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            CriticalPart2 = -CND(z2)
        End If
    End Function
    Private Function CriticalPart3(ByVal id As Integer, ByVal I As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal v As Double) As Double
        Dim z1 As Double, z2 As Double
        If id = 1 Then
            z1 = (Log(I) + v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            z2 = (Log(I) - v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            CriticalPart3 = I * CND(z1) - CND(z2)
        ElseIf id = 2 Then
            z1 = (-Log(I) + v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            z2 = (-Log(I) - v ^ 2 / 2 * (T2 - t1)) / (v * Sqrt(T2 - t1))
            CriticalPart3 = CND(z1) - I * CND(z2)
        End If
    End Function


    '// Options on the maximum or minimum of two risky assets
    Public Function OptionsOnTheMaxMin(ByVal TypeFlag As String, ByVal S1 As Double, ByVal S2 As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, _
            ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim v As Double, rho1 As Double, rho2 As Double
        Dim d As Double, y1 As Double, y2 As Double

        v = Sqrt(v1 ^ 2 + v2 ^ 2 - 2 * rho * v1 * v2)
        rho1 = (v1 - rho * v2) / v
        rho2 = (v2 - rho * v1) / v
        d = (Log(S1 / S2) + (b1 - b2 + v ^ 2 / 2) * T) / (v * Sqrt(T))
        y1 = (Log(S1 / X) + (b1 + v1 ^ 2 / 2) * T) / (v1 * Sqrt(T))
        y2 = (Log(S2 / X) + (b2 + v2 ^ 2 / 2) * T) / (v2 * Sqrt(T))

        If TypeFlag = "cmin" Then
            OptionsOnTheMaxMin = S1 * Exp((b1 - r) * T) * CBND(y1, -d, -rho1) + S2 * Exp((b2 - r) * T) * CBND(y2, d - v * Sqrt(T), -rho2) - X * Exp(-r * T) * CBND(y1 - v1 * Sqrt(T), y2 - v2 * Sqrt(T), rho)
        ElseIf TypeFlag = "cmax" Then
            OptionsOnTheMaxMin = S1 * Exp((b1 - r) * T) * CBND(y1, d, rho1) + S2 * Exp((b2 - r) * T) * CBND(y2, -d + v * Sqrt(T), rho2) - X * Exp(-r * T) * (1 - CBND(-y1 + v1 * Sqrt(T), -y2 + v2 * Sqrt(T), rho))
        ElseIf TypeFlag = "pmin" Then
            OptionsOnTheMaxMin = X * Exp(-r * T) - S1 * Exp((b1 - r) * T) + EuropeanExchangeOption(S1, S2, 1, 1, T, r, b1, b2, v1, v2, rho) + OptionsOnTheMaxMin("cmin", S1, S2, X, T, r, b1, b2, v1, v2, rho)
        ElseIf TypeFlag = "pmax" Then
            OptionsOnTheMaxMin = X * Exp(-r * T) - S2 * Exp((b2 - r) * T) - EuropeanExchangeOption(S1, S2, 1, 1, T, r, b1, b2, v1, v2, rho) + OptionsOnTheMaxMin("cmax", S1, S2, X, T, r, b1, b2, v1, v2, rho)
        End If
    End Function


    '// Spread option approximation
    Function SpreadApproximation(ByVal CallPutFlag As String, ByVal f1 As Double, ByVal f2 As Double, ByVal X As Double, ByVal T As Double, _
                    ByVal r As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim v As Double, F As Double
        Dim d1 As Double, d2 As Double

        v = Sqrt(v1 ^ 2 + (v2 * f2 / (f2 + X)) ^ 2 - 2 * rho * v1 * v2 * f2 / (f2 + X))
        F = f1 / (f2 + X)

        SpreadApproximation = GBlackScholes(CallPutFlag, F, 1, T, r, 0, v) * (f2 + X)
    End Function


    '// Floating strike lookback options
    Function FloatingStrikeLookback(ByVal CallPutFlag As String, ByVal S As Double, ByVal SMin As Double, ByVal SMax As Double, ByVal T As Double, _
                ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim a1 As Double, a2 As Double, m As Double

        If CallPutFlag = "c" Then
            m = SMin
        ElseIf CallPutFlag = "p" Then
            m = SMax
        End If

        a1 = (Log(S / m) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        a2 = a1 - v * Sqrt(T)

        If CallPutFlag = "c" Then
            FloatingStrikeLookback = S * Exp((b - r) * T) * CND(a1) - m * Exp(-r * T) * CND(a2) + _
            Exp(-r * T) * v ^ 2 / (2 * b) * S * ((S / m) ^ (-2 * b / v ^ 2) * CND(-a1 + 2 * b / v * Sqrt(T)) - Exp(b * T) * CND(-a1))
        ElseIf CallPutFlag = "p" Then
            FloatingStrikeLookback = m * Exp(-r * T) * CND(-a2) - S * Exp((b - r) * T) * CND(-a1) + _
            Exp(-r * T) * v ^ 2 / (2 * b) * S * (-(S / m) ^ (-2 * b / v ^ 2) * CND(a1 - 2 * b / v * Sqrt(T)) + Exp(b * T) * CND(a1))
        End If
    End Function


    '// Fixed strike lookback options
    Public Function FixedStrikeLookback(ByVal CallPutFlag As String, ByVal S As Double, ByVal SMin As Double, ByVal SMax As Double, ByVal X As Double, _
                     ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double
        Dim e1 As Double, e2 As Double, m As Double

        If CallPutFlag = "c" Then
            m = SMax
        ElseIf CallPutFlag = "p" Then
            m = SMin
        End If

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)
        e1 = (Log(S / m) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        e2 = e1 - v * Sqrt(T)

        If CallPutFlag = "c" And X > m Then
            FixedStrikeLookback = S * Exp((b - r) * T) * CND(d1) - X * Exp(-r * T) * CND(d2) _
            + S * Exp(-r * T) * v ^ 2 / (2 * b) * (-(S / X) ^ (-2 * b / v ^ 2) * CND(d1 - 2 * b / v * Sqrt(T)) + Exp(b * T) * CND(d1))
        ElseIf CallPutFlag = "c" And X <= m Then
            FixedStrikeLookback = Exp(-r * T) * (m - X) + S * Exp((b - r) * T) * CND(e1) - Exp(-r * T) * m * CND(e2) _
            + S * Exp(-r * T) * v ^ 2 / (2 * b) * (-(S / m) ^ (-2 * b / v ^ 2) * CND(e1 - 2 * b / v * Sqrt(T)) + Exp(b * T) * CND(e1))
        ElseIf CallPutFlag = "p" And X < m Then
            FixedStrikeLookback = -S * Exp((b - r) * T) * CND(-d1) + X * Exp(-r * T) * CND(-d1 + v * Sqrt(T)) _
            + S * Exp(-r * T) * v ^ 2 / (2 * b) * ((S / X) ^ (-2 * b / v ^ 2) * CND(-d1 + 2 * b / v * Sqrt(T)) - Exp(b * T) * CND(-d1))
        ElseIf CallPutFlag = "p" And X >= m Then
            FixedStrikeLookback = Exp(-r * T) * (X - m) - S * Exp((b - r) * T) * CND(-e1) + Exp(-r * T) * m * CND(-e1 + v * Sqrt(T)) _
            + Exp(-r * T) * v ^ 2 / (2 * b) * S * ((S / m) ^ (-2 * b / v ^ 2) * CND(-e1 + 2 * b / v * Sqrt(T)) - Exp(b * T) * CND(-e1))
        End If
    End Function


    '// Partial-time floating strike lookback options
    Public Function PartialFloatLB(ByVal CallPutFlag As String, ByVal S As Double, ByVal SMin As Double, ByVal SMax As Double, ByVal t1 As Double, _
                    ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double, ByVal lambda As Double)

        Dim d1 As Double, d2 As Double
        Dim e1 As Double, e2 As Double
        Dim f1 As Double, f2 As Double
        Dim g1 As Double, g2 As Double, m As Double
        Dim part1 As Double, part2 As Double, part3 As Double

        If CallPutFlag = "c" Then
            m = SMin
        ElseIf CallPutFlag = "p" Then
            m = SMax
        End If

        d1 = (Log(S / m) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        d2 = d1 - v * Sqrt(T2)
        e1 = (b + v ^ 2 / 2) * (T2 - t1) / (v * Sqrt(T2 - t1))
        e2 = e1 - v * Sqrt(T2 - t1)
        f1 = (Log(S / m) + (b + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        f2 = f1 - v * Sqrt(t1)
        g1 = Log(lambda) / (v * Sqrt(T2))
        g2 = Log(lambda) / (v * Sqrt(T2 - t1))

        If CallPutFlag = "c" Then
            part1 = S * Exp((b - r) * T2) * CND(d1 - g1) - lambda * m * Exp(-r * T2) * CND(d2 - g1)
            part2 = Exp(-r * T2) * v ^ 2 / (2 * b) * lambda * S * ((S / m) ^ (-2 * b / v ^ 2) * CBND(-f1 + 2 * b * Sqrt(t1) / v, -d1 + 2 * b * Sqrt(T2) / v - g1, Sqrt(t1 / T2)) _
            - Exp(b * T2) * lambda ^ (2 * b / v ^ 2) * CBND(-d1 - g1, e1 + g2, -Sqrt(1 - t1 / T2))) _
            + S * Exp((b - r) * T2) * CBND(-d1 + g1, e1 - g2, -Sqrt(1 - t1 / T2))
            part3 = Exp(-r * T2) * lambda * m * CBND(-f2, d2 - g1, -Sqrt(t1 / T2)) _
            - Exp(-b * (T2 - t1)) * Exp((b - r) * T2) * (1 + v ^ 2 / (2 * b)) * lambda * S * CND(e2 - g2) * CND(-f1)

        ElseIf CallPutFlag = "p" Then
            part1 = lambda * m * Exp(-r * T2) * CND(-d2 + g1) - S * Exp((b - r) * T2) * CND(-d1 + g1)
            part2 = -Exp(-r * T2) * v ^ 2 / (2 * b) * lambda * S * ((S / m) ^ (-2 * b / v ^ 2) * CBND(f1 - 2 * b * Sqrt(t1) / v, d1 - 2 * b * Sqrt(T2) / v + g1, Sqrt(t1 / T2)) _
            - Exp(b * T2) * lambda ^ (2 * b / v ^ 2) * CBND(d1 + g1, -e1 - g2, -Sqrt(1 - t1 / T2))) _
            - S * Exp((b - r) * T2) * CBND(d1 - g1, -e1 + g2, -Sqrt(1 - t1 / T2))
            part3 = -Exp(-r * T2) * lambda * m * CBND(f2, -d2 + g1, -Sqrt(t1 / T2)) _
            + Exp(-b * (T2 - t1)) * Exp((b - r) * T2) * (1 + v ^ 2 / (2 * b)) * lambda * S * CND(-e2 + g2) * CND(f1)
        End If
        PartialFloatLB = part1 + part2 + part3
    End Function


    '// Partial-time fixed strike lookback options
    Public Function PartialFixedLB(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal t1 As Double, _
                    ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double
        Dim e1 As Double, e2 As Double
        Dim f1 As Double, f2 As Double

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        d2 = d1 - v * Sqrt(T2)
        e1 = ((b + v ^ 2 / 2) * (T2 - t1)) / (v * Sqrt(T2 - t1))
        e2 = e1 - v * Sqrt(T2 - t1)
        f1 = (Log(S / X) + (b + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        f2 = f1 - v * Sqrt(t1)
        If CallPutFlag = "c" Then
            PartialFixedLB = S * Exp((b - r) * T2) * CND(d1) - Exp(-r * T2) * X * CND(d2) + S * Exp(-r * T2) * v ^ 2 / (2 * b) * (-(S / X) ^ (-2 * b / v ^ 2) * CBND(d1 - 2 * b * Sqrt(T2) / v, -f1 + 2 * b * Sqrt(t1) / v, -Sqrt(t1 / T2)) + Exp(b * T2) * CBND(e1, d1, Sqrt(1 - t1 / T2))) - S * Exp((b - r) * T2) * CBND(-e1, d1, -Sqrt(1 - t1 / T2)) - X * Exp(-r * T2) * CBND(f2, -d2, -Sqrt(t1 / T2)) + Exp(-b * (T2 - t1)) * (1 - v ^ 2 / (2 * b)) * S * Exp((b - r) * T2) * CND(f1) * CND(-e2)
        ElseIf CallPutFlag = "p" Then
            PartialFixedLB = X * Exp(-r * T2) * CND(-d2) - S * Exp((b - r) * T2) * CND(-d1) + S * Exp(-r * T2) * v ^ 2 / (2 * b) * ((S / X) ^ (-2 * b / v ^ 2) * CBND(-d1 + 2 * b * Sqrt(T2) / v, f1 - 2 * b * Sqrt(t1) / v, -Sqrt(t1 / T2)) - Exp(b * T2) * CBND(-e1, -d1, Sqrt(1 - t1 / T2))) + S * Exp((b - r) * T2) * CBND(e1, -d1, -Sqrt(1 - t1 / T2)) + X * Exp(-r * T2) * CBND(-f2, d2, -Sqrt(t1 / T2)) - Exp(-b * (T2 - t1)) * (1 - v ^ 2 / (2 * b)) * S * Exp((b - r) * T2) * CND(-f1) * CND(e2)
        End If
    End Function


    '// Extreme spread options
    Public Function ExtremeSpreadOption(ByVal TypeFlag As Integer, ByVal S As Double, ByVal SMin As Double, ByVal SMax As Double, ByVal t1 As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim m As Double, Mo As Double
        Dim mu1 As Double, mu As Double
        Dim kappa As Integer, eta As Integer

        If TypeFlag = 1 Or TypeFlag = 3 Then
            eta = 1
        Else
            eta = -1
        End If
        If TypeFlag = 1 Or TypeFlag = 2 Then
            kappa = 1
        Else
            kappa = -1
        End If

        If kappa * eta = 1 Then
            Mo = SMax
        ElseIf kappa * eta = -1 Then
            Mo = SMin
        End If

        mu1 = b - v ^ 2 / 2
        mu = mu1 + v ^ 2
        m = Log(Mo / S)
        If kappa = 1 Then '// Extreme Spread Option
            ExtremeSpreadOption = eta * (S * Exp((b - r) * T) * (1 + v ^ 2 / (2 * b)) * CND(eta * (-m + mu * T) / (v * Sqrt(T))) - Exp(-r * (T - t1)) * S * Exp((b - r) * T) * (1 + v ^ 2 / (2 * b)) * CND(eta * (-m + mu * t1) / (v * Sqrt(t1))) _
            + Exp(-r * T) * Mo * CND(eta * (m - mu1 * T) / (v * Sqrt(T))) - Exp(-r * T) * Mo * v ^ 2 / (2 * b) * Exp(2 * mu1 * m / v ^ 2) * CND(eta * (-m - mu1 * T) / (v * Sqrt(T))) _
            - Exp(-r * T) * Mo * CND(eta * (m - mu1 * t1) / (v * Sqrt(t1))) + Exp(-r * T) * Mo * v ^ 2 / (2 * b) * Exp(2 * mu1 * m / v ^ 2) * CND(eta * (-m - mu1 * t1) / (v * Sqrt(t1))))
        ElseIf kappa = -1 Then  '// Reverse Extreme Spread Option
            ExtremeSpreadOption = -eta * (S * Exp((b - r) * T) * (1 + v ^ 2 / (2 * b)) * CND(eta * (m - mu * T) / (v * Sqrt(T))) + Exp(-r * T) * Mo * CND(eta * (-m + mu1 * T) / (v * Sqrt(T))) _
            - Exp(-r * T) * Mo * v ^ 2 / (2 * b) * Exp(2 * mu1 * m / v ^ 2) * CND(eta * (m + mu1 * T) / (v * Sqrt(T))) - S * Exp((b - r) * T) * (1 + v ^ 2 / (2 * b)) * CND(eta * (-mu * (T - t1)) / (v * Sqrt(T - t1))) _
            - Exp(-r * (T - t1)) * S * Exp((b - r) * T) * (1 - v ^ 2 / (2 * b)) * CND(eta * (mu1 * (T - t1)) / (v * Sqrt(T - t1))))
        End If
    End Function


    '// Standard barrier options
    Function StandardBarrier(ByVal TypeFlag As String, ByVal S As Double, ByVal X As Double, ByVal H As Double, ByVal K As Double, ByVal T As Double, _
                ByVal r As Double, ByVal b As Double, ByVal v As Double)

        Dim mu As Double
        Dim lambda As Double
        Dim X1 As Double, X2 As Double
        Dim y1 As Double, y2 As Double
        Dim Z As Double

        Dim eta As Integer    'Binary variable that can take the value of 1 or -1
        Dim phi As Integer    'Binary variable that can take the value of 1 or -1

        Dim f1 As Double    'Equal to formula "A" in the book
        Dim f2 As Double    'Equal to formula "B" in the book
        Dim f3 As Double    'Equal to formula "C" in the book
        Dim f4 As Double    'Equal to formula "D" in the book
        Dim f5 As Double    'Equal to formula "E" in the book
        Dim f6 As Double    'Equal to formula "F" in the book

        mu = (b - v ^ 2 / 2) / v ^ 2
        lambda = Sqrt(mu ^ 2 + 2 * r / v ^ 2)
        X1 = Log(S / X) / (v * Sqrt(T)) + (1 + mu) * v * Sqrt(T)
        X2 = Log(S / H) / (v * Sqrt(T)) + (1 + mu) * v * Sqrt(T)
        y1 = Log(H ^ 2 / (S * X)) / (v * Sqrt(T)) + (1 + mu) * v * Sqrt(T)
        y2 = Log(H / S) / (v * Sqrt(T)) + (1 + mu) * v * Sqrt(T)
        Z = Log(H / S) / (v * Sqrt(T)) + lambda * v * Sqrt(T)

        If TypeFlag = "cdi" Or TypeFlag = "cdo" Then
            eta = 1
            phi = 1
        ElseIf TypeFlag = "cui" Or TypeFlag = "cuo" Then
            eta = -1
            phi = 1
        ElseIf TypeFlag = "pdi" Or TypeFlag = "pdo" Then
            eta = 1
            phi = -1
        ElseIf TypeFlag = "pui" Or TypeFlag = "puo" Then
            eta = -1
            phi = -1
        End If

        f1 = phi * S * Exp((b - r) * T) * CND(phi * X1) - phi * X * Exp(-r * T) * CND(phi * X1 - phi * v * Sqrt(T))
        f2 = phi * S * Exp((b - r) * T) * CND(phi * X2) - phi * X * Exp(-r * T) * CND(phi * X2 - phi * v * Sqrt(T))
        f3 = phi * S * Exp((b - r) * T) * (H / S) ^ (2 * (mu + 1)) * CND(eta * y1) - phi * X * Exp(-r * T) * (H / S) ^ (2 * mu) * CND(eta * y1 - eta * v * Sqrt(T))
        f4 = phi * S * Exp((b - r) * T) * (H / S) ^ (2 * (mu + 1)) * CND(eta * y2) - phi * X * Exp(-r * T) * (H / S) ^ (2 * mu) * CND(eta * y2 - eta * v * Sqrt(T))
        f5 = K * Exp(-r * T) * (CND(eta * X2 - eta * v * Sqrt(T)) - (H / S) ^ (2 * mu) * CND(eta * y2 - eta * v * Sqrt(T)))
        f6 = K * ((H / S) ^ (mu + lambda) * CND(eta * Z) + (H / S) ^ (mu - lambda) * CND(eta * Z - 2 * eta * lambda * v * Sqrt(T)))


        If X > H Then
            Select Case TypeFlag
                Case Is = "cdi"
                    StandardBarrier = f3 + f5
                Case Is = "cui"
                    StandardBarrier = f1 + f5
                Case Is = "pdi"
                    StandardBarrier = f2 - f3 + f4 + f5
                Case Is = "pui"
                    StandardBarrier = f1 - f2 + f4 + f5
                Case Is = "cdo"
                    StandardBarrier = f1 - f3 + f6
                Case Is = "cuo"
                    StandardBarrier = f6
                Case Is = "pdo"
                    StandardBarrier = f1 - f2 + f3 - f4 + f6
                Case Is = "puo"
                    StandardBarrier = f2 - f4 + f6
            End Select
        ElseIf X < H Then
            Select Case TypeFlag
                Case Is = "cdi"
                    StandardBarrier = f1 - f2 + f4 + f5
                Case Is = "cui"
                    StandardBarrier = f2 - f3 + f4 + f5
                Case Is = "pdi"
                    StandardBarrier = f1 + f5
                Case Is = "pui"
                    StandardBarrier = f3 + f5
                Case Is = "cdo"
                    StandardBarrier = f2 + f6 - f4
                Case Is = "cuo"
                    StandardBarrier = f1 - f2 + f3 - f4 + f6
                Case Is = "pdo"
                    StandardBarrier = f6
                Case Is = "puo"
                    StandardBarrier = f1 - f3 + f6
            End Select
        End If
    End Function


    '// Double barrier options
    Function DoubleBarrier(ByVal TypeFlag As String, ByVal S As Double, ByVal X As Double, ByVal L As Double, ByVal U As Double, ByVal T As Double, _
            ByVal r As Double, ByVal b As Double, ByVal v As Double, ByVal delta1 As Double, ByVal delta2 As Double) As Double

        Dim E As Double, F As Double
        Dim Sum1 As Double, Sum2 As Double
        Dim d1 As Double, d2 As Double
        Dim d3 As Double, d4 As Double
        Dim mu1 As Double, mu2 As Double, mu3 As Double
        Dim OutValue As Double, n As Integer

        F = U * Exp(delta1 * T)
        E = L * Exp(delta1 * T)
        Sum1 = 0
        Sum2 = 0
        If TypeFlag = "co" Or TypeFlag = "ci" Then
            For n = -5 To 5
                d1 = (Log(S * U ^ (2 * n) / (X * L ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d2 = (Log(S * U ^ (2 * n) / (F * L ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d3 = (Log(L ^ (2 * n + 2) / (X * S * U ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d4 = (Log(L ^ (2 * n + 2) / (F * S * U ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                mu1 = 2 * (b - delta2 - n * (delta1 - delta2)) / v ^ 2 + 1
                mu2 = 2 * n * (delta1 - delta2) / v ^ 2
                mu3 = 2 * (b - delta2 + n * (delta1 - delta2)) / v ^ 2 + 1
                Sum1 = Sum1 + (U ^ n / L ^ n) ^ mu1 * (L / S) ^ mu2 * (CND(d1) - CND(d2)) - (L ^ (n + 1) / (U ^ n * S)) ^ mu3 * (CND(d3) - CND(d4))
                Sum2 = Sum2 + (U ^ n / L ^ n) ^ (mu1 - 2) * (L / S) ^ mu2 * (CND(d1 - v * Sqrt(T)) - CND(d2 - v * Sqrt(T))) - (L ^ (n + 1) / (U ^ n * S)) ^ (mu3 - 2) * (CND(d3 - v * Sqrt(T)) - CND(d4 - v * Sqrt(T)))
            Next
            OutValue = S * Exp((b - r) * T) * Sum1 - X * Exp(-r * T) * Sum2
        ElseIf TypeFlag = "po" Or TypeFlag = "pi" Then
            For n = -5 To 5
                d1 = (Log(S * U ^ (2 * n) / (E * L ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d2 = (Log(S * U ^ (2 * n) / (X * L ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d3 = (Log(L ^ (2 * n + 2) / (E * S * U ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                d4 = (Log(L ^ (2 * n + 2) / (X * S * U ^ (2 * n))) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
                mu1 = 2 * (b - delta2 - n * (delta1 - delta2)) / v ^ 2 + 1
                mu2 = 2 * n * (delta1 - delta2) / v ^ 2
                mu3 = 2 * (b - delta2 + n * (delta1 - delta2)) / v ^ 2 + 1
                Sum1 = Sum1 + (U ^ n / L ^ n) ^ mu1 * (L / S) ^ mu2 * (CND(d1) - CND(d2)) - (L ^ (n + 1) / (U ^ n * S)) ^ mu3 * (CND(d3) - CND(d4))
                Sum2 = Sum2 + (U ^ n / L ^ n) ^ (mu1 - 2) * (L / S) ^ mu2 * (CND(d1 - v * Sqrt(T)) - CND(d2 - v * Sqrt(T))) - (L ^ (n + 1) / (U ^ n * S)) ^ (mu3 - 2) * (CND(d3 - v * Sqrt(T)) - CND(d4 - v * Sqrt(T)))
            Next
            OutValue = X * Exp(-r * T) * Sum2 - S * Exp((b - r) * T) * Sum1
        End If
        If TypeFlag = "co" Or TypeFlag = "po" Then
            DoubleBarrier = OutValue
        ElseIf TypeFlag = "ci" Then
            DoubleBarrier = GBlackScholes("c", S, X, T, r, b, v) - OutValue
        ElseIf TypeFlag = "pi" Then
            DoubleBarrier = GBlackScholes("p", S, X, T, r, b, v) - OutValue
        End If
    End Function


    '// Partial-time singel asset barrier options
    Public Function PartialTimeBarrier(ByVal TypeFlag As String, ByVal S As Double, ByVal X As Double, ByVal H As Double, _
                    ByVal t1 As Double, ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double
        Dim f1 As Double, f2 As Double
        Dim e1 As Double, e2 As Double
        Dim e3 As Double, e4 As Double
        Dim g1 As Double, g2 As Double
        Dim g3 As Double, g4 As Double
        Dim mu As Double, rho As Double, eta As Integer
        Dim z1 As Double, z2 As Double, z3 As Double
        Dim z4 As Double, z5 As Double, z6 As Double
        Dim z7 As Double, z8 As Double

        If TypeFlag = "cdoA" Then
            eta = 1
        ElseIf TypeFlag = "cuoA" Then
            eta = -1
        End If

        d1 = (Log(S / X) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        d2 = d1 - v * Sqrt(T2)
        f1 = (Log(S / X) + 2 * Log(H / S) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        f2 = f1 - v * Sqrt(T2)
        e1 = (Log(S / H) + (b + v ^ 2 / 2) * t1) / (v * Sqrt(t1))
        e2 = e1 - v * Sqrt(t1)
        e3 = e1 + 2 * Log(H / S) / (v * Sqrt(t1))
        e4 = e3 - v * Sqrt(t1)
        mu = (b - v ^ 2 / 2) / v ^ 2
        rho = Sqrt(t1 / T2)
        g1 = (Log(S / H) + (b + v ^ 2 / 2) * T2) / (v * Sqrt(T2))
        g2 = g1 - v * Sqrt(T2)
        g3 = g1 + 2 * Log(H / S) / (v * Sqrt(T2))
        g4 = g3 - v * Sqrt(T2)

        z1 = CND(e2) - (H / S) ^ (2 * mu) * CND(e4)
        z2 = CND(-e2) - (H / S) ^ (2 * mu) * CND(-e4)
        z3 = CBND(g2, e2, rho) - (H / S) ^ (2 * mu) * CBND(g4, -e4, -rho)
        z4 = CBND(-g2, -e2, rho) - (H / S) ^ (2 * mu) * CBND(-g4, e4, -rho)
        z5 = CND(e1) - (H / S) ^ (2 * (mu + 1)) * CND(e3)
        z6 = CND(-e1) - (H / S) ^ (2 * (mu + 1)) * CND(-e3)
        z7 = CBND(g1, e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(g3, -e3, -rho)
        z8 = CBND(-g1, -e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(-g3, e3, -rho)

        If TypeFlag = "cdoA" Or TypeFlag = "cuoA" Then '// call down-and out and up-and-out type A
            PartialTimeBarrier = S * Exp((b - r) * T2) * (CBND(d1, eta * e1, eta * rho) - (H / S) ^ (2 * (mu + 1)) * CBND(f1, eta * e3, eta * rho)) _
            - X * Exp(-r * T2) * (CBND(d2, eta * e2, eta * rho) - (H / S) ^ (2 * mu) * CBND(f2, eta * e4, eta * rho))
        ElseIf TypeFlag = "cdoB2" And X < H Then  '// call down-and-out type B2
            PartialTimeBarrier = S * Exp((b - r) * T2) * (CBND(g1, e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(g3, -e3, -rho)) _
            - X * Exp(-r * T2) * (CBND(g2, e2, rho) - (H / S) ^ (2 * mu) * CBND(g4, -e4, -rho))
        ElseIf TypeFlag = "cdoB2" And X > H Then
            PartialTimeBarrier = PartialTimeBarrier("coB1", S, X, H, t1, T2, r, b, v)
        ElseIf TypeFlag = "cuoB2" And X < H Then  '// call up-and-out type B2
            PartialTimeBarrier = S * Exp((b - r) * T2) * (CBND(-g1, -e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(-g3, e3, -rho)) _
            - X * Exp(-r * T2) * (CBND(-g2, -e2, rho) - (H / S) ^ (2 * mu) * CBND(-g4, e4, -rho)) _
            - S * Exp((b - r) * T2) * (CBND(-d1, -e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(e3, -f1, -rho)) _
            + X * Exp(-r * T2) * (CBND(-d2, -e2, rho) - (H / S) ^ (2 * mu) * CBND(e4, -f2, -rho))
        ElseIf TypeFlag = "coB1" And X > H Then  '// call out type B1
            PartialTimeBarrier = S * Exp((b - r) * T2) * (CBND(d1, e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(f1, -e3, -rho)) _
            - X * Exp(-r * T2) * (CBND(d2, e2, rho) - (H / S) ^ (2 * mu) * CBND(f2, -e4, -rho))
        ElseIf TypeFlag = "coB1" And X < H Then
            PartialTimeBarrier = S * Exp((b - r) * T2) * (CBND(-g1, -e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(-g3, e3, -rho)) _
            - X * Exp(-r * T2) * (CBND(-g2, -e2, rho) - (H / S) ^ (2 * mu) * CBND(-g4, e4, -rho)) _
            - S * Exp((b - r) * T2) * (CBND(-d1, -e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(-f1, e3, -rho)) _
            + X * Exp(-r * T2) * (CBND(-d2, -e2, rho) - (H / S) ^ (2 * mu) * CBND(-f2, e4, -rho)) _
            + S * Exp((b - r) * T2) * (CBND(g1, e1, rho) - (H / S) ^ (2 * (mu + 1)) * CBND(g3, -e3, -rho)) _
            - X * Exp(-r * T2) * (CBND(g2, e2, rho) - (H / S) ^ (2 * mu) * CBND(g4, -e4, -rho))
        ElseIf TypeFlag = "pdoA" Then  '// put down-and out and up-and-out type A
            PartialTimeBarrier = PartialTimeBarrier("cdoA", S, X, H, t1, T2, r, b, v) - S * Exp((b - r) * T2) * z5 + X * Exp(-r * T2) * z1
        ElseIf TypeFlag = "puoA" Then
            PartialTimeBarrier = PartialTimeBarrier("cuoA", S, X, H, t1, T2, r, b, v) - S * Exp((b - r) * T2) * z6 + X * Exp(-r * T2) * z2
        ElseIf TypeFlag = "poB1" Then  '// put out type B1
            PartialTimeBarrier = PartialTimeBarrier("coB1", S, X, H, t1, T2, r, b, v) - S * Exp((b - r) * T2) * z8 + X * Exp(-r * T2) * z4 - S * Exp((b - r) * T2) * z7 + X * Exp(-r * T2) * z3
        ElseIf TypeFlag = "pdoB2" Then  '// put down-and-out type B2
            PartialTimeBarrier = PartialTimeBarrier("cdoB2", S, X, H, t1, T2, r, b, v) - S * Exp((b - r) * T2) * z7 + X * Exp(-r * T2) * z3
        ElseIf TypeFlag = "puoB2" Then  '// put up-and-out type B2
            PartialTimeBarrier = PartialTimeBarrier("cuoB2", S, X, H, t1, T2, r, b, v) - S * Exp((b - r) * T2) * z8 + X * Exp(-r * T2) * z4
        End If
    End Function


    '// Two asset barrier options
    Public Function TwoAssetBarrier(ByVal TypeFlag As String, ByVal S1 As Double, ByVal S2 As Double, ByVal X As Double, ByVal H As Double, _
                    ByVal T As Double, ByVal r As Double, ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim d1 As Double, d2 As Double, d3 As Double, d4 As Double
        Dim e1 As Double, e2 As Double, e3 As Double, e4 As Double
        Dim mu1 As Double, mu2 As Double
        Dim eta As Integer    'Binary variable: 1 for call options and -1 for put options
        Dim phi As Integer    'Binary variable: 1 for up options and -1 for down options
        Dim KnockOutValue As Double

        mu1 = b1 - v1 ^ 2 / 2
        mu2 = b2 - v2 ^ 2 / 2

        d1 = (Log(S1 / X) + (mu1 + v1 ^ 2 / 2) * T) / (v1 * Sqrt(T))
        d2 = d1 - v1 * Sqrt(T)
        d3 = d1 + 2 * rho * Log(H / S2) / (v2 * Sqrt(T))
        d4 = d2 + 2 * rho * Log(H / S2) / (v2 * Sqrt(T))
        e1 = (Log(H / S2) - (mu2 + rho * v1 * v2) * T) / (v2 * Sqrt(T))
        e2 = e1 + rho * v1 * Sqrt(T)
        e3 = e1 - 2 * Log(H / S2) / (v2 * Sqrt(T))
        e4 = e2 - 2 * Log(H / S2) / (v2 * Sqrt(T))

        If TypeFlag = "cuo" Or TypeFlag = "cui" Then
            eta = 1 : phi = 1
        ElseIf TypeFlag = "cdo" Or TypeFlag = "cdi" Then
            eta = 1 : phi = -1
        ElseIf TypeFlag = "puo" Or TypeFlag = "pui" Then
            eta = -1 : phi = 1
        ElseIf TypeFlag = "pdo" Or TypeFlag = "pdi" Then
            eta = -1 : phi = -1
        End If
        KnockOutValue = eta * S1 * Exp((b1 - r) * T) * (CBND(eta * d1, phi * e1, -eta * phi * rho) _
        - Exp(2 * (mu2 + rho * v1 * v2) * Log(H / S2) / v2 ^ 2) * CBND(eta * d3, phi * e3, -eta * phi * rho)) - eta * Exp(-r * T) * X * (CBND(eta * d2, phi * e2, -eta * phi * rho) _
        - Exp(2 * mu2 * Log(H / S2) / v2 ^ 2) * CBND(eta * d4, phi * e4, -eta * phi * rho))
        If TypeFlag = "cuo" Or TypeFlag = "cdo" Or TypeFlag = "puo" Or TypeFlag = "pdo" Then
            TwoAssetBarrier = KnockOutValue
        ElseIf TypeFlag = "cui" Or TypeFlag = "cdi" Then
            TwoAssetBarrier = GBlackScholes("c", S1, X, T, r, b1, v1) - KnockOutValue
        ElseIf TypeFlag = "pui" Or TypeFlag = "pdi" Then
            TwoAssetBarrier = GBlackScholes("p", S1, X, T, r, b1, v1) - KnockOutValue
        End If

    End Function


    '// Partial-time two asset barrier options
    Public Function PartialTimeTwoAssetBarrier(ByVal TypeFlag As String, ByVal S1 As Double, ByVal S2 As Double, ByVal X As Double, ByVal H As Double, ByVal t1 As Double, ByVal T2 As Double, _
                    ByVal r As Double, ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim d1 As Double, d2 As Double
        Dim d3 As Double, d4 As Double
        Dim e1 As Double, e2 As Double
        Dim e3 As Double, e4 As Double
        Dim mu1 As Double, mu2 As Double
        Dim OutBarrierValue As Double

        Dim eta As Integer
        Dim phi As Integer

        If TypeFlag = "cdo" Or TypeFlag = "pdo" Or TypeFlag = "cdi" Or TypeFlag = "pdi" Then
            phi = -1
        Else
            phi = 1
        End If

        If TypeFlag = "cdo" Or TypeFlag = "cuo" Or TypeFlag = "cdi" Or TypeFlag = "cui" Then
            eta = 1
        Else
            eta = -1
        End If
        mu1 = b1 - v1 ^ 2 / 2
        mu2 = b2 - v2 ^ 2 / 2
        d1 = (Log(S1 / X) + (mu1 + v1 ^ 2) * T2) / (v1 * Sqrt(T2))
        d2 = d1 - v1 * Sqrt(T2)
        d3 = d1 + 2 * rho * Log(H / S2) / (v2 * Sqrt(T2))
        d4 = d2 + 2 * rho * Log(H / S2) / (v2 * Sqrt(T2))
        e1 = (Log(H / S2) - (mu2 + rho * v1 * v2) * t1) / (v2 * Sqrt(t1))
        e2 = e1 + rho * v1 * Sqrt(t1)
        e3 = e1 - 2 * Log(H / S2) / (v2 * Sqrt(t1))
        e4 = e2 - 2 * Log(H / S2) / (v2 * Sqrt(t1))

        OutBarrierValue = eta * S1 * Exp((b1 - r) * T2) * (CBND(eta * d1, phi * e1, -eta * phi * rho * Sqrt(t1 / T2)) - Exp(2 * Log(H / S2) * (mu2 + rho * v1 * v2) / (v2 ^ 2)) _
        * CBND(eta * d3, phi * e3, -eta * phi * rho * Sqrt(t1 / T2))) _
        - eta * Exp(-r * T2) * X * (CBND(eta * d2, phi * e2, -eta * phi * rho * Sqrt(t1 / T2)) - Exp(2 * Log(H / S2) * mu2 / (v2 ^ 2)) _
        * CBND(eta * d4, phi * e4, -eta * phi * rho * Sqrt(t1 / T2)))

        If TypeFlag = "cdo" Or TypeFlag = "cuo" Or TypeFlag = "pdo" Or TypeFlag = "puo" Then
            PartialTimeTwoAssetBarrier = OutBarrierValue
        ElseIf TypeFlag = "cui" Or TypeFlag = "cdi" Then
            PartialTimeTwoAssetBarrier = GBlackScholes("c", S1, X, T2, r, b1, v1) - OutBarrierValue
        ElseIf TypeFlag = "pui" Or TypeFlag = "pdi" Then
            PartialTimeTwoAssetBarrier = GBlackScholes("p", S1, X, T2, r, b1, v1) - OutBarrierValue
        End If
    End Function



    '// Look-barrier options
    Public Function LookBarrier(ByVal TypeFlag As String, ByVal S As Double, ByVal X As Double, ByVal H As Double, ByVal t1 As Double, ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim hh As Double
        Dim K As Double, mu1 As Double, mu2 As Double
        Dim rho As Double, eta As Double, m As Double
        Dim g1 As Double, g2 As Double
        Dim OutValue As Double, part1 As Double, part2 As Double, part3 As Double, part4 As Double

        hh = Log(H / S)
        K = Log(X / S)
        mu1 = b - v ^ 2 / 2
        mu2 = b + v ^ 2 / 2
        rho = Sqrt(t1 / T2)

        If TypeFlag = "cuo" Or TypeFlag = "cui" Then
            eta = 1
            m = Min(hh, K)
        ElseIf TypeFlag = "pdo" Or TypeFlag = "pdi" Then
            eta = -1
            m = Max(hh, K)
        End If

        g1 = (CND(eta * (hh - mu2 * t1) / (v * Sqrt(t1))) - Exp(2 * mu2 * hh / v ^ 2) * CND(eta * (-hh - mu2 * t1) / (v * Sqrt(t1)))) _
            - (CND(eta * (m - mu2 * t1) / (v * Sqrt(t1))) - Exp(2 * mu2 * hh / v ^ 2) * CND(eta * (m - 2 * hh - mu2 * t1) / (v * Sqrt(t1))))
        g2 = (CND(eta * (hh - mu1 * t1) / (v * Sqrt(t1))) - Exp(2 * mu1 * hh / v ^ 2) * CND(eta * (-hh - mu1 * t1) / (v * Sqrt(t1)))) _
            - (CND(eta * (m - mu1 * t1) / (v * Sqrt(t1))) - Exp(2 * mu1 * hh / v ^ 2) * CND(eta * (m - 2 * hh - mu1 * t1) / (v * Sqrt(t1))))

        part1 = S * Exp((b - r) * T2) * (1 + v ^ 2 / (2 * b)) * (CBND(eta * (m - mu2 * t1) / (v * Sqrt(t1)), eta * (-K + mu2 * T2) / (v * Sqrt(T2)), -rho) - Exp(2 * mu2 * hh / v ^ 2) _
            * CBND(eta * (m - 2 * hh - mu2 * t1) / (v * Sqrt(t1)), eta * (2 * hh - K + mu2 * T2) / (v * Sqrt(T2)), -rho))
        part2 = -Exp(-r * T2) * X * (CBND(eta * (m - mu1 * t1) / (v * Sqrt(t1)), eta * (-K + mu1 * T2) / (v * Sqrt(T2)), -rho) _
            - Exp(2 * mu1 * hh / v ^ 2) * CBND(eta * (m - 2 * hh - mu1 * t1) / (v * Sqrt(t1)), eta * (2 * hh - K + mu1 * T2) / (v * Sqrt(T2)), -rho))
        part3 = -Exp(-r * T2) * v ^ 2 / (2 * b) * (S * (S / X) ^ (-2 * b / v ^ 2) * CBND(eta * (m + mu1 * t1) / (v * Sqrt(t1)), eta * (-K - mu1 * T2) / (v * Sqrt(T2)), -rho) _
            - H * (H / X) ^ (-2 * b / v ^ 2) * CBND(eta * (m - 2 * hh + mu1 * t1) / (v * Sqrt(t1)), eta * (2 * hh - K - mu1 * T2) / (v * Sqrt(T2)), -rho))
        part4 = S * Exp((b - r) * T2) * ((1 + v ^ 2 / (2 * b)) * CND(eta * mu2 * (T2 - t1) / (v * Sqrt(T2 - t1))) + Exp(-b * (T2 - t1)) * (1 - v ^ 2 / (2 * b)) _
            * CND(eta * (-mu1 * (T2 - t1)) / (v * Sqrt(T2 - t1)))) * g1 - Exp(-r * T2) * X * g2
        OutValue = eta * (part1 + part2 + part3 + part4)

        If TypeFlag = "cuo" Or TypeFlag = "pdo" Then
            LookBarrier = OutValue
        ElseIf TypeFlag = "cui" Then
            LookBarrier = PartialFixedLB("c", S, X, t1, T2, r, b, v) - OutValue
        ElseIf TypeFlag = "pdi" Then
            LookBarrier = PartialFixedLB("p", S, X, t1, T2, r, b, v) - OutValue
        End If
    End Function


    '// Discrete barrier monitoring adjustment
    Public Function DiscreteAdjustedBarrier(ByVal S As Double, ByVal H As Double, ByVal v As Double, ByVal dt As Double) As Double

        If H > S Then
            DiscreteAdjustedBarrier = H * Exp(0.5826 * v * Sqrt(dt))
        ElseIf H < S Then
            DiscreteAdjustedBarrier = H * Exp(-0.5826 * v * Sqrt(dt))
        End If
    End Function


    '// Soft barrier options
    Public Function SoftBarrier(ByVal TypeFlag As String, ByVal S As Double, ByVal X As Double, _
                                ByVal L As Double, ByVal U As Double, ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim mu As Double
        Dim d1 As Double, d2 As Double
        Dim d3 As Double, d4 As Double
        Dim e1 As Double, e2 As Double
        Dim e3 As Double, e4 As Double
        Dim lambda1 As Double, lambda2 As Double
        Dim Value As Double, eta As Integer

        If TypeFlag = "cdi" Or TypeFlag = "cdo" Then
            eta = 1
        Else
            eta = -1
        End If

        mu = (b + v ^ 2 / 2) / v ^ 2
        lambda1 = Exp(-1 / 2 * v ^ 2 * T * (mu + 0.5) * (mu - 0.5))
        lambda2 = Exp(-1 / 2 * v ^ 2 * T * (mu - 0.5) * (mu - 1.5))
        d1 = Log(U ^ 2 / (S * X)) / (v * Sqrt(T)) + mu * v * Sqrt(T)
        d2 = d1 - (mu + 0.5) * v * Sqrt(T)
        d3 = Log(U ^ 2 / (S * X)) / (v * Sqrt(T)) + (mu - 1) * v * Sqrt(T)
        d4 = d3 - (mu - 0.5) * v * Sqrt(T)
        e1 = Log(L ^ 2 / (S * X)) / (v * Sqrt(T)) + mu * v * Sqrt(T)
        e2 = e1 - (mu + 0.5) * v * Sqrt(T)
        e3 = Log(L ^ 2 / (S * X)) / (v * Sqrt(T)) + (mu - 1) * v * Sqrt(T)
        e4 = e3 - (mu - 0.5) * v * Sqrt(T)

        Value = eta * 1 / (U - L) * (S * Exp((b - r) * T) * S ^ (-2 * mu) _
        * (S * X) ^ (mu + 0.5) / (2 * (mu + 0.5)) _
        * ((U ^ 2 / (S * X)) ^ (mu + 0.5) * CND(eta * d1) - lambda1 * CND(eta * d2) _
        - (L ^ 2 / (S * X)) ^ (mu + 0.5) * CND(eta * e1) + lambda1 * CND(eta * e2)) _
        - X * Exp(-r * T) * S ^ (-2 * (mu - 1)) _
        * (S * X) ^ (mu - 0.5) / (2 * (mu - 0.5)) _
        * ((U ^ 2 / (S * X)) ^ (mu - 0.5) * CND(eta * d3) - lambda2 * CND(eta * d4) _
        - (L ^ 2 / (S * X)) ^ (mu - 0.5) * CND(eta * e3) + lambda2 * CND(eta * e4)))

        If TypeFlag = "cdi" Or TypeFlag = "pui" Then
            SoftBarrier = Value
        ElseIf TypeFlag = "cdo" Then
            SoftBarrier = GBlackScholes("c", S, X, T, r, b, v) - Value
        ElseIf TypeFlag = "puo" Then
            SoftBarrier = GBlackScholes("p", S, X, T, r, b, v) - Value
        End If
    End Function


    '// Gap options
    Public Function GapOption(ByVal CallPutFlag As String, ByVal S As Double, ByVal X1 As Double, ByVal X2 As Double, _
                    ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X1) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        If CallPutFlag = "c" Then
            GapOption = S * Exp((b - r) * T) * CND(d1) - X2 * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            GapOption = X2 * Exp(-r * T) * CND(-d2) - S * Exp((b - r) * T) * CND(-d1)
        End If
    End Function


    '// Cash-or-nothing options
    Public Function CashOrNothing(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal K As Double, ByVal T As Double, _
                    ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d As Double

        d = (Log(S / X) + (b - v ^ 2 / 2) * T) / (v * Sqrt(T))

        If CallPutFlag = "c" Then
            CashOrNothing = K * Exp(-r * T) * CND(d)
        ElseIf CallPutFlag = "p" Then
            CashOrNothing = K * Exp(-r * T) * CND(-d)
        End If
    End Function


    '// Two asset cash-or-nothing options
    Public Function TwoAssetCashOrNothing(ByVal TypeFlag As Integer, ByVal S1 As Double, ByVal S2 As Double, ByVal X1 As Double, ByVal X2 As Double, ByVal K As Double, ByVal T As Double, ByVal r As Double, _
                    ByVal b1 As Double, ByVal b2 As Double, ByVal v1 As Double, ByVal v2 As Double, ByVal rho As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S1 / X1) + (b1 - v1 ^ 2 / 2) * T) / (v1 * Sqrt(T))
        d2 = (Log(S2 / X2) + (b2 - v2 ^ 2 / 2) * T) / (v2 * Sqrt(T))

        If TypeFlag = 1 Then
            TwoAssetCashOrNothing = K * Exp(-r * T) * CBND(d1, d2, rho)
        ElseIf TypeFlag = 2 Then
            TwoAssetCashOrNothing = K * Exp(-r * T) * CBND(-d1, -d2, rho)
        ElseIf TypeFlag = 3 Then
            TwoAssetCashOrNothing = K * Exp(-r * T) * CBND(d1, -d2, -rho)
        ElseIf TypeFlag = 4 Then
            TwoAssetCashOrNothing = K * Exp(-r * T) * CBND(-d1, d2, -rho)
        End If
    End Function


    '// Asset-or-nothing options
    Public Function AssetOrNothing(ByVal CallPutFlag As String, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, _
                    ByVal b As Double, ByVal v As Double) As Double

        Dim d As Double

        d = (Log(S / X) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))

        If CallPutFlag = "c" Then
            AssetOrNothing = S * Exp((b - r) * T) * CND(d)
        ElseIf CallPutFlag = "p" Then
            AssetOrNothing = S * Exp((b - r) * T) * CND(-d)
        End If
    End Function


    '// Supershare options
    Public Function SuperShare(ByVal S As Double, ByVal XL As Double, ByVal XH As Double, ByVal T As Double, _
                    ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / XL) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = (Log(S / XH) + (b + v ^ 2 / 2) * T) / (v * Sqrt(T))

        SuperShare = S * Exp((b - r) * T) / XL * (CND(d1) - CND(d2))
    End Function


    '// Binary barrier options
    Public Function BinaryBarrier(ByVal TypeFlag As Integer, ByVal S As Double, ByVal X As Double, ByVal H As Double, ByVal K As Double, _
                    ByVal T As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double, ByVal eta As Integer, ByVal phi As Integer) As Double

        '// TypeFlag:  Value 1 to 28 dependent on binary option type,
        '//            look in the book for spesifications.

        Dim X1 As Double, X2 As Double
        Dim y1 As Double, y2 As Double
        Dim Z As Double, mu As Double, lambda As Double
        Dim a1 As Double, a2 As Double, a3 As Double, a4 As Double, a5 As Double
        Dim b1 As Double, b2 As Double, b3 As Double, b4 As Double

        mu = (b - v ^ 2 / 2) / v ^ 2
        lambda = Sqrt(mu ^ 2 + 2 * r / v ^ 2)
        X1 = Log(S / X) / (v * Sqrt(T)) + (mu + 1) * v * Sqrt(T)
        X2 = Log(S / H) / (v * Sqrt(T)) + (mu + 1) * v * Sqrt(T)
        y1 = Log(H ^ 2 / (S * X)) / (v * Sqrt(T)) + (mu + 1) * v * Sqrt(T)
        y2 = Log(H / S) / (v * Sqrt(T)) + (mu + 1) * v * Sqrt(T)
        Z = Log(H / S) / (v * Sqrt(T)) + lambda * v * Sqrt(T)

        a1 = S * Exp((b - r) * T) * CND(phi * X1)
        b1 = K * Exp(-r * T) * CND(phi * X1 - phi * v * Sqrt(T))
        a2 = S * Exp((b - r) * T) * CND(phi * X2)
        b2 = K * Exp(-r * T) * CND(phi * X2 - phi * v * Sqrt(T))
        a3 = S * Exp((b - r) * T) * (H / S) ^ (2 * (mu + 1)) * CND(eta * y1)
        b3 = K * Exp(-r * T) * (H / S) ^ (2 * mu) * CND(eta * y1 - eta * v * Sqrt(T))
        a4 = S * Exp((b - r) * T) * (H / S) ^ (2 * (mu + 1)) * CND(eta * y2)
        b4 = K * Exp(-r * T) * (H / S) ^ (2 * mu) * CND(eta * y2 - eta * v * Sqrt(T))
        a5 = K * ((H / S) ^ (mu + lambda) * CND(eta * Z) + (H / S) ^ (mu - lambda) * CND(eta * Z - 2 * eta * lambda * v * Sqrt(T)))

        If X > H Then
            Select Case TypeFlag
                Case Is < 5
                    BinaryBarrier = a5
                Case Is < 7
                    BinaryBarrier = b2 + b4
                Case Is < 9
                    BinaryBarrier = a2 + a4
                Case Is < 11
                    BinaryBarrier = b2 - b4
                Case Is < 13
                    BinaryBarrier = a2 - a4
                Case Is = 13
                    BinaryBarrier = b3
                Case Is = 14
                    BinaryBarrier = b3
                Case Is = 15
                    BinaryBarrier = a3
                Case Is = 16
                    BinaryBarrier = a1
                Case Is = 17
                    BinaryBarrier = b2 - b3 + b4
                Case Is = 18
                    BinaryBarrier = b1 - b2 + b4
                Case Is = 19
                    BinaryBarrier = a2 - a3 + a4
                Case Is = 20
                    BinaryBarrier = a1 - a2 + a3
                Case Is = 21
                    BinaryBarrier = b1 - b3
                Case Is = 22
                    BinaryBarrier = 0
                Case Is = 23
                    BinaryBarrier = a1 - a3
                Case Is = 24
                    BinaryBarrier = 0
                Case Is = 25
                    BinaryBarrier = b1 - b2 + b3 - b4
                Case Is = 26
                    BinaryBarrier = b2 - b4
                Case Is = 27
                    BinaryBarrier = a1 - a2 + a3 - a4
                Case Is = 28
                    BinaryBarrier = a2 - a4
            End Select
        ElseIf X < H Then
            Select Case TypeFlag
                Case Is < 5
                    BinaryBarrier = a5
                Case Is < 7
                    BinaryBarrier = b2 + b4
                Case Is < 9
                    BinaryBarrier = a2 + a4
                Case Is < 11
                    BinaryBarrier = b2 - b4
                Case Is < 13
                    BinaryBarrier = a2 - a4
                Case Is = 13
                    BinaryBarrier = b1 - b2 + b4
                Case Is = 14
                    BinaryBarrier = b2 - b3 + b4
                Case Is = 15
                    BinaryBarrier = a1 - a2 + a4
                Case Is = 16
                    BinaryBarrier = a2 - a3 + a4
                Case Is = 17
                    BinaryBarrier = b1
                Case Is = 18
                    BinaryBarrier = b3
                Case Is = 19
                    BinaryBarrier = a1
                Case Is = 20
                    BinaryBarrier = a3
                Case Is = 21
                    BinaryBarrier = b2 - b4
                Case Is = 22
                    BinaryBarrier = b1 - b2 + b3 - b4
                Case Is = 23
                    BinaryBarrier = a2 - a4
                Case Is = 24
                    BinaryBarrier = a1 - a2 + a3 - a4
                Case Is = 25
                    BinaryBarrier = 0
                Case Is = 26
                    BinaryBarrier = b1 - b3
                Case Is = 27
                    BinaryBarrier = 0
                Case Is = 28
                    BinaryBarrier = a1 - a3
            End Select
        End If
    End Function


    '// Geometric average rate option
    Public Function GeometricAverageRateOption(ByVal CallPutFlag As String, ByVal S As Double, ByVal SA As Double, ByVal X As Double, _
                    ByVal T As Double, ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double


        Dim t1 As Double 'Observed or realized time period
        Dim bA As Double, vA As Double

        bA = 1 / 2 * (b - v ^ 2 / 6)
        vA = v / Sqrt(3)

        t1 = T - T2

        If t1 > 0 Then
            X = (t1 + T2) / T2 * X - t1 / T2 * SA
            GeometricAverageRateOption = GBlackScholes(CallPutFlag, S, X, T2, r, bA, vA) * T2 / (t1 + T2)
        ElseIf t1 = 0 Then
            GeometricAverageRateOption = GBlackScholes(CallPutFlag, S, X, T, r, bA, vA)
        End If

    End Function


    '// Arithmetic average rate option
    Public Function TurnbullWakemanAsian(ByVal CallPutFlag As String, ByVal S As Double, ByVal SA As Double, ByVal X As Double, _
                ByVal T As Double, ByVal T2 As Double, ByVal tau As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim m1 As Double, m2 As Double, t1 As Double
        Dim bA As Double, vA As Double

        m1 = (Exp(b * T) - Exp(b * tau)) / (b * (T - tau))
        m2 = 2 * Exp((2 * b + v ^ 2) * T) / ((b + v ^ 2) * (2 * b + v ^ 2) * (T - tau) ^ 2) _
        + 2 * Exp((2 * b + v ^ 2) * tau) / (b * (T - tau) ^ 2) * (1 / (2 * b + v ^ 2) - Exp(b * (T - tau)) / (b + v ^ 2))

        bA = Log(m1) / T
        vA = Sqrt(Log(m2) / T - 2 * bA)
        t1 = T - T2

        If t1 > 0 Then
            X = T / T2 * X - t1 / T2 * SA
            TurnbullWakemanAsian = GBlackScholes(CallPutFlag, S, X, T2, r, bA, vA) * T2 / T
        Else
            TurnbullWakemanAsian = GBlackScholes(CallPutFlag, S, X, T2, r, bA, vA)
        End If
    End Function


    '// Arithmetic average rate option
    Public Function LevyAsian(ByVal CallPutFlag As String, ByVal S As Double, ByVal SA As Double, ByVal X As Double, _
                    ByVal T As Double, ByVal T2 As Double, ByVal r As Double, ByVal b As Double, ByVal v As Double) As Double

        Dim SE As Double
        Dim m As Double, d As Double
        Dim Sv As Double, XStar As Double
        Dim d1 As Double, d2 As Double

        SE = S / (T * b) * (Exp((b - r) * T2) - Exp(-r * T2))
        m = 2 * S ^ 2 / (b + v ^ 2) * ((Exp((2 * b + v ^ 2) * T2) - 1) / (2 * b + v ^ 2) - (Exp(b * T2) - 1) / b)
        d = m / (T ^ 2)
        Sv = Log(d) - 2 * (r * T2 + Log(SE))
        XStar = X - (T - T2) / T * SA
        d1 = 1 / Sqrt(Sv) * (Log(d) / 2 - Log(XStar))
        d2 = d1 - Sqrt(Sv)

        If CallPutFlag = "c" Then
            LevyAsian = SE * CND(d1) - XStar * Exp(-r * T2) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            LevyAsian = (SE * CND(d1) - XStar * Exp(-r * T2) * CND(d2)) - SE + XStar * Exp(-r * T2)
        End If
    End Function


    '// Foreign equity option struck in domestic currency
    Public Function ForEquOptInDomCur(ByVal CallPutFlag As String, ByVal E As Double, ByVal S As Double, ByVal X As Double, ByVal T As Double, _
        ByVal r As Double, ByVal q As Double, ByVal vS As Double, ByVal vE As Double, ByVal rho As Double) As Double

        Dim v As Double, d1 As Double, d2 As Double

        v = Sqrt(vE ^ 2 + vS ^ 2 + 2 * rho * vE * vS)
        d1 = (Log(E * S / X) + (r - q + v ^ 2 / 2) * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        If CallPutFlag = "c" Then
            ForEquOptInDomCur = E * S * Exp(-q * T) * CND(d1) - X * Exp(-r * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            ForEquOptInDomCur = X * Exp(-r * T) * CND(-d2) - E * S * Exp(-q * T) * CND(-d1)
        End If
    End Function


    '// Fixed exchange rate foreign equity options-- Quantos
    Public Function Quanto(ByVal CallPutFlag As String, ByVal Ep As Double, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, _
                    ByVal rf As Double, ByVal q As Double, ByVal vS As Double, ByVal vE As Double, ByVal rho As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(S / X) + (rf - q - rho * vS * vE + vS ^ 2 / 2) * T) / (vS * Sqrt(T))
        d2 = d1 - vS * Sqrt(T)

        If CallPutFlag = "c" Then
            Quanto = Ep * (S * Exp((rf - r - q - rho * vS * vE) * T) * CND(d1) - X * Exp(-r * T) * CND(d2))
        ElseIf CallPutFlag = "p" Then
            Quanto = Ep * (X * Exp(-r * T) * CND(-d2) - S * Exp((rf - r - q - rho * vS * vE) * T) * CND(-d1))
        End If
    End Function


    '// Equity linked foreign exchange option
    Public Function EquityLinkedFXO(ByVal CallPutFlag As String, ByVal E As Double, ByVal S As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, _
                    ByVal rf As Double, ByVal q As Double, ByVal vS As Double, ByVal vE As Double, ByVal rho As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(E / X) + (r - rf + rho * vS * vE + vE ^ 2 / 2) * T) / (vE * Sqrt(T))
        d2 = d1 - vE * Sqrt(T)

        If CallPutFlag = "c" Then
            EquityLinkedFXO = E * S * Exp(-q * T) * CND(d1) - X * S * Exp((rf - r - q - rho * vS * vE) * T) * CND(d2)
        ElseIf CallPutFlag = "p" Then
            EquityLinkedFXO = X * S * Exp((rf - r - q - rho * vS * vE) * T) * CND(-d2) - E * S * Exp(-q * T) * CND(-d1)
        End If
    End Function


    '// Takeover foreign exchange options
    Public Function TakeoverFXoption(ByVal v As Double, ByVal b As Double, ByVal E As Double, ByVal X As Double, ByVal T As Double, ByVal r As Double, ByVal rf As Double, ByVal vV As Double, ByVal vE As Double, ByVal rho As Double) As Double

        Dim a1 As Double, a2 As Double

        a1 = (Log(v / b) + (rf - rho * vE * vV - vV ^ 2 / 2) * T) / (vV * Sqrt(T))
        a2 = (Log(E / X) + (r - rf - vE ^ 2 / 2) * T) / (vE * Sqrt(T))

        TakeoverFXoption = b * (E * Exp(-rf * T) * CBND(a2 + vE * Sqrt(T), -a1 - rho * vE * Sqrt(T), -rho) _
        - X * Exp(-r * T) * CBND(-a1, a2, -rho))

    End Function

End Module
