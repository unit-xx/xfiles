Option Explicit On     'Requires that all variables to be declared explicitly.
Option Compare Text 'Uppercase letters to be equivalent to lowercase letters.
Imports System.Math

Module InterestRate

    '//  Black-76 European swaption
    Public Function Swaption(ByVal CallPutFlag As String, ByVal t1 As Double, ByVal m As Double, ByVal F As Double, ByVal X As Double, ByVal T As Double, _
                    ByVal r As Double, ByVal v As Double) As Double

        Dim d1 As Double, d2 As Double

        d1 = (Log(F / X) + v ^ 2 / 2 * T) / (v * Sqrt(T))
        d2 = d1 - v * Sqrt(T)

        If CallPutFlag = "c" Then 'Payer swaption
            Swaption = ((1 - 1 / (1 + F / m) ^ (t1 * m)) / F) * Exp(-r * T) * (F * CND(d1) - X * CND(d2))
        ElseIf CallPutFlag = "p" Then  'Receiver swaption
            Swaption = ((1 - 1 / (1 + F / m) ^ (t1 * m)) / F) * Exp(-r * T) * (X * CND(-d2) - F * CND(-d1))
        End If

    End Function


    '// Vasicek: options on zero coupon bonds
    Function VasicekBondOption(ByVal CallPutFlag As String, ByVal F As Double, ByVal X As Double, ByVal tau As Double, ByVal T As Double, _
            ByVal r As Double, ByVal theta As Double, ByVal kappa As Double, ByVal v As Double) As Double


        Dim PtT As Double, Pt_tau As Double
        Dim H As Double, vp As Double

        X = X / F
        PtT = VasicekBondPrice(0, T, r, theta, kappa, v)
        Pt_tau = VasicekBondPrice(0, tau, r, theta, kappa, v)
        vp = Sqrt(v ^ 2 * (1 - Exp(-2 * kappa * T)) / (2 * kappa)) * (1 - Exp(-kappa * (tau - T))) / kappa

        H = 1 / vp * Log(Pt_tau / (PtT * X)) + vp / 2

        If CallPutFlag = "c" Then
            VasicekBondOption = F * (Pt_tau * CND(H) - X * PtT * CND(H - vp))
        Else
            VasicekBondOption = F * (X * PtT * CND(-H + vp) - Pt_tau * CND(-H))
        End If
    End Function


    '// Vasicek: value zero coupon bond
    Public Function VasicekBondPrice(ByVal t1 As Double, ByVal T As Double, ByVal r As Double, ByVal theta As Double, ByVal kappa As Double, ByVal v As Double) As Double
        Dim BtT As Double, AtT As Double, PtT As Double

        BtT = (1 - Exp(-kappa * (T - t1))) / kappa
        AtT = Exp((BtT - T + t1) * (kappa ^ 2 * theta - v ^ 2 / 2) / kappa ^ 2 - v ^ 2 * BtT ^ 2 / (4 * kappa))
        PtT = AtT * Exp(-BtT * r)
        VasicekBondPrice = PtT
    End Function

End Module
