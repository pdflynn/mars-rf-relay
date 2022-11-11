%% ECE 4805 Senior Design Project
%  RF Relay for Mars Ingenuity AHD
%  Link Analysis
%  References
%  [1] https://www.researchgate.net/publication/241232512_Mars_Background_Noise_Temperatures_Received_by_Spacecraft_Antennas 
%  [2] Ali Grami Digital Communications book
%  [3] https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.03.01_20/en_30230702v010301a.pdf
clear;clc;close all;

%% Assumptions
% Constants
k_B = physconst('boltzmann');   % Boltzmann Constant
c = physconst('lightspeed');    % Vacuum propagation speed

% Operating Parameters
B = 30e6;        % System bandwidth (MHz)
f_c = 2.45e9;    % System center frequency (GHz)
R_s = 30000e3;      % Symbol rate (symbols per second)
BER = 10^-5;     % Bit Error Rate Requirement

% Transmitter Figure of Merit: EIRP
G_tx = 5;     % Transmitter Antenna Gain (dBi)
P_tx = 15.0;     % Transmitter Power Output (dBm)

% Physical Path Assumptions
d = 1e3:1:25e3;   % Distance between AHDs (m) - Parameterized
L_atm = 0.5;     % Atmospheric Loss (dB) on Mars

% Receiver Figure of Merit: G/T
% Note: More research is needed for an accurate estimate (see [1])
G_rx = 5;     % Receiver Antenna Gain (dBi)
T_s = 280;       % Receiver System Noise Temperature (K)
B_n = 30e6;      % Receiver Noise Bandwidth - SDR IF bandwidth (MHz)

%% Calculate Gains, Losses, and determine C=Pr and N
N = 10.*log10(k_B .* T_s .* B_n);    % Noise Power, dBW
L_p = 20.*log10((4 .* pi .* d .* f_c)./ c); % FSPL, dB
% Reminder below: convert EIRP to dBW from dBm
Pr = (G_tx - 30) + P_tx + G_rx - L_p - L_atm;  % Received power

C_N = Pr - N; % Carrier-to-noise ratio, dB

%% Calculate EbN0 and create BER function handles
% BER function for BPSK [2]
PBER_B = @(EN) qfunc(sqrt(2.*EN));
% BER function handle for M-PSK [2]
PBER = @(M, EN) (2 ./ log2(M)) .* qfunc(sqrt(2.*log2(M).*EN) .* sin(pi./M));
% Possible values of M
M = [2 4 8 16 32];
% Determine Eb/N0
Eb_N0_linear = (10.^(0.1.*C_N)) .* (B ./ R_s);
Eb_N0 = 10.*log10(Eb_N0_linear);

%% Calculate BER Requirement for M-PSK (no coding)
% FIXED: you were putting dB EbN0 into the q-function
%        so this was causing an error and inaccurate
%        BERs. Make sure to use linear!
BER_Curve = zeros(length(d), length(M));
BER_Curve(:, 1) = PBER_B(Eb_N0_linear);
% TODO: don't do these calculations here, add a "spectral efficiency"
%       variable (bits per symbol) and then you can actually include
%       coding from DVB-S2x MODCODs in this script too
fprintf("Data rate with BPSK: %2.2f kbps\n", R_s.*log2(M(1)).*1e-3);
for i=2:length(M)
    BER_Curve(:, i) = PBER(M(i), Eb_N0_linear);
    fprintf("Data rate with %i-PSK: %2.2f kbps\n", M(i), R_s.*log2(M(i)).*1e-3);
end

%% Other calculations (distance parameterization)
% IGNORE THIS SECTION FOR NOW (work in progress)
R_s_query = 10e3:5:1000e3;
R_b_query = zeros(length(R_s_query), length(M));
EbN0_Needed = 0:0.01:250;

% Determine BPSK needed EbN0 for required BER
PBER_B_query = PBER_B(EbN0_Needed);
[~, indx_BPSK_needed_EbN0] = min(abs(PBER_B_query - BER));
BPSK_needed_EbN0 = EbN0_Needed(indx_BPSK_needed_EbN0);
R_b_query(:, 1) = R_s_query.*log2(M(1));

% Determine MPSK needed EbN0 for required BER
needed_EbN0 = zeros(length(M), 1);
needed_EbN0(1) = BPSK_needed_EbN0;
for i=2:length(M)
    R_b_query(:, i) = R_s_query.*log2(M(i));
    PBER_M_query = PBER(M(i), EbN0_Needed);
    [~, indx] = min(abs(PBER_M_query - BER));
    tmp_EbN0 = EbN0_Needed(indx);
    needed_EbN0(i) = tmp_EbN0;
end

% Determine distance for needed EbN0
[~, indx_BPSK] = min(abs(Eb_N0 - needed_EbN0(1)));
d_BPSK = d(indx_BPSK);
max_dist = zeros(length(M), 1);
for i=1:length(M)
    [~, indx] = min(abs(Eb_N0 - needed_EbN0(i)));
    max_dist(i, 1) = d(indx);
end

% TODO: finish this part. Should ultimately have an array that has the
% data rate for each constellation, and then we want to correlate that
% with the EbNo (and thus distance) that we need for that data rate, then
% plot that so we know the max distance where each one works.
%% Create Plots
figure;
plot(d.*1e-3, C_N);
xlim([d(1).*1e-3 d(end).*1e-3]);
title("Carrier to Noise Ratio versus Distance");
xlabel("Distance d from Transmitter [km]");
ylabel("^{C}/_{N} [dB]");

figure;
plot(d.*1e-3, Eb_N0);
xlim([d(1).*1e-3 10]);
title("Bit Energy to Noise Power Spectral Density versus Distance");
xlabel("Distance d from Transmitter [km]");
ylabel("^{E_b}/_{N_0} [dB]");

figure;
% Show BER versus distance for fixed symbol rate
subplot(2,1,1);
hold on;
for i=1:length(M)
    plot(d.*1e-3, BER_Curve(:, i), 'LineWidth', 2);
end
grid on;
set(gca, 'YScale', 'log');
title("Expected Bit Error Rate vs. Distance (No Coding)");
xlabel("Distance d from Transmitter [km]");
xlim([d(1).*1e-3 d(end).*1e-3]);
ylim([1e-12 1]);
ylabel("BER");
yline(BER, 'Label', 'Required BER: 10^{-5}');
legend(["BPSK", "QPSK", "8PSK", "16PSK", "32PSK", ""], 'Location', 'Southeast');

% Show constellation max distance for required BER
subplot(2,1,2);
plot(M, max_dist, 'sr', 'MarkerSize', 10, 'MarkerEdgeColor', 'red', 'MarkerFaceColor', [1 .6 .6]);
xlabel("Constellation Size");
ylabel("Maximum Distance for Required BER");


%% DVB-S2X Section - data rates we can achieve with DVB-S2x MODCODs
% Goal here: Data rate versus distance based on Es/N0
% [3] calls a Frame Error Rate (FER) of 10^-5 to be considered
% "quasi error-free." We will take this figure as meeting our BER
% requirement of 10^-6, but I am unsure of how to convert between the two.

% DVB-S2 information read / etc
MODCODs = readtable('DVB_S2x.csv');
DVB_Constellation = MODCODs{:, 1};
DVB_CodeRate      = MODCODs{:, 2};
DVB_SpectralEff   = MODCODs{:, 3};
DVB_IdealEsN0     = MODCODs{:, 4};

alpha = 0.25; % roll-off factor for pulse shaping
SpectralEff = DVB_SpectralEff ./ (1+alpha); % Note 4 from Table 20a [3]

% Determine maximum data rate versus distance based on ideal Es/N0
DVB_bitrates = zeros(1, length(d));
DVB_MODCOD_selected(1:length(d)) = {''};

Es_N0_linear = (10.^(0.1 .* C_N)) .* (B ./ R_s);
Es_N0 = 10.*log10(Es_N0_linear);
for i=1:length(d)
    % Based on Es/N0, find the highest MODCOD possible
    Es_N0_available = Es_N0(i);
    possible_vals = Es_N0_available >= DVB_IdealEsN0;
    indx = find(possible_vals == 1, 1, 'last');
    DVB_MODCOD_selected(i) = cellstr([DVB_Constellation{indx} ' ' DVB_CodeRate{indx}]);
    
    % Determine spectral efficiency available
    SpectralEff_avail = DVB_SpectralEff(indx);
    if isempty(SpectralEff_avail)
        SpectralEff_avail = 0;
    end
    
    % Determine the bitrate based on spectral efficiency
    DVB_bitrates(i) = B .* SpectralEff_avail;
end

figure;
plot(d.*1e-3, DVB_bitrates.*1e-6);
xlim([d(1).*1e-3 d(end).*1e-3]);
title("DVB-S2x QEF Bitrate versus Distance");
xlabel("Distance d from Transmitter [km]");
ylabel("Bitrate [Mbps]");