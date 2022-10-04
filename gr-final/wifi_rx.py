#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Wifi Rx
# GNU Radio version: 3.9.8.0

from distutils.version import StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio import gr
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy
from gnuradio.qtgui import Range, RangeWidget
from PyQt5 import QtCore
import correctiq
import ieee802_11



from gnuradio import qtgui

class wifi_rx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Wifi Rx", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Wifi Rx")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "wifi_rx")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.window_size = window_size = 48
        self.sync_length = sync_length = 320
        self.sens = sens = 0.56
        self.samp_rate = samp_rate = 10e6
        self.rf_gain = rf_gain = 0
        self.lo_offset = lo_offset = 0
        self.gain = gain = 0.5
        self.freq = freq = 912e6
        self.chan_est = chan_est = 0

        ##################################################
        # Blocks
        ##################################################
        self._sens_range = Range(0, 1, 0.01, 0.56, 200)
        self._sens_win = RangeWidget(self._sens_range, self.set_sens, "Sensitivity", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._sens_win)
        # Create the options list
        self._samp_rate_options = [5000000.0, 10000000.0, 20000000.0]
        # Create the labels list
        self._samp_rate_labels = ['5 MHz', '10 MHz', '20 MHz']
        # Create the combo box
        self._samp_rate_tool_bar = Qt.QToolBar(self)
        self._samp_rate_tool_bar.addWidget(Qt.QLabel("'samp_rate'" + ": "))
        self._samp_rate_combo_box = Qt.QComboBox()
        self._samp_rate_tool_bar.addWidget(self._samp_rate_combo_box)
        for _label in self._samp_rate_labels: self._samp_rate_combo_box.addItem(_label)
        self._samp_rate_callback = lambda i: Qt.QMetaObject.invokeMethod(self._samp_rate_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._samp_rate_options.index(i)))
        self._samp_rate_callback(self.samp_rate)
        self._samp_rate_combo_box.currentIndexChanged.connect(
            lambda i: self.set_samp_rate(self._samp_rate_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._samp_rate_tool_bar)
        self._rf_gain_range = Range(-12, 61, 2, 0, 200)
        self._rf_gain_win = RangeWidget(self._rf_gain_range, self.set_rf_gain, "RF Gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_win)
        self._gain_range = Range(0, 10, 0.1, 0.5, 200)
        self._gain_win = RangeWidget(self._gain_range, self.set_gain, "'gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._gain_win)
        # Create the options list
        self._chan_est_options = [0, 1, 2, 3]
        # Create the labels list
        self._chan_est_labels = ['LS', 'LMS', 'Linear Comb', 'STA']
        # Create the combo box
        # Create the radio buttons
        self._chan_est_group_box = Qt.QGroupBox("'chan_est'" + ": ")
        self._chan_est_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._chan_est_button_group = variable_chooser_button_group()
        self._chan_est_group_box.setLayout(self._chan_est_box)
        for i, _label in enumerate(self._chan_est_labels):
            radio_button = Qt.QRadioButton(_label)
            self._chan_est_box.addWidget(radio_button)
            self._chan_est_button_group.addButton(radio_button, i)
        self._chan_est_callback = lambda i: Qt.QMetaObject.invokeMethod(self._chan_est_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._chan_est_options.index(i)))
        self._chan_est_callback(self.chan_est)
        self._chan_est_button_group.buttonClicked[int].connect(
            lambda i: self.set_chan_est(self._chan_est_options[i]))
        self.top_layout.addWidget(self._chan_est_group_box)
        self.soapy_limesdr_source_0 = None
        dev = 'driver=lime'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_limesdr_source_0 = soapy.source(dev, "fc32", 1, '',
                                  stream_args, tune_args, settings)
        self.soapy_limesdr_source_0.set_sample_rate(0, samp_rate)
        self.soapy_limesdr_source_0.set_bandwidth(0, 0.0)
        self.soapy_limesdr_source_0.set_frequency(0, freq)
        self.soapy_limesdr_source_0.set_frequency_correction(0, 0)
        self.soapy_limesdr_source_0.set_gain(0, min(max(rf_gain, -12.0), 61.0))
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            48*10, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis(-2, 2)
        self.qtgui_const_sink_x_0.set_x_axis(-2, 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        # Create the options list
        self._lo_offset_options = [0, 6000000.0, 11000000.0]
        # Create the labels list
        self._lo_offset_labels = ['0', '6000000.0', '11000000.0']
        # Create the combo box
        self._lo_offset_tool_bar = Qt.QToolBar(self)
        self._lo_offset_tool_bar.addWidget(Qt.QLabel("'lo_offset'" + ": "))
        self._lo_offset_combo_box = Qt.QComboBox()
        self._lo_offset_tool_bar.addWidget(self._lo_offset_combo_box)
        for _label in self._lo_offset_labels: self._lo_offset_combo_box.addItem(_label)
        self._lo_offset_callback = lambda i: Qt.QMetaObject.invokeMethod(self._lo_offset_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._lo_offset_options.index(i)))
        self._lo_offset_callback(self.lo_offset)
        self._lo_offset_combo_box.currentIndexChanged.connect(
            lambda i: self.set_lo_offset(self._lo_offset_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._lo_offset_tool_bar)
        self.ieee802_11_sync_short_0 = ieee802_11.sync_short(sens, 2, False, False)
        self.ieee802_11_sync_long_0 = ieee802_11.sync_long(sync_length, False, False)
        self.ieee802_11_parse_mac_0 = ieee802_11.parse_mac(False, True)
        self.ieee802_11_frame_equalizer_0 = ieee802_11.frame_equalizer(ieee802_11.Equalizer(chan_est), freq, samp_rate, False, False)
        self.ieee802_11_decode_mac_0 = ieee802_11.decode_mac(True, False)
        self.fft_vxx_0 = fft.fft_vcc(64, True, window.rectangular(64), True, 1)
        self.fft_filter_xxx_0 = filter.fft_filter_ccc(1, [3.475465564406477e-05, 3.921664392692037e-05, 4.3666452256729826e-05, 4.810490281670354e-05, 5.253248309600167e-05, 5.694930223398842e-05, 6.135496369097382e-05, 6.574857980012894e-05, 7.012864807620645e-05, 7.449306576745585e-05, 7.88389952504076e-05, 8.3162885857746e-05, 8.746036473894492e-05, 9.172626596409827e-05, 9.595452866051346e-05, 0.00010013821156462654, 0.00010426943481434137, 0.00010833935084519908, 0.00011233818077016622, 0.00011625513434410095, 0.00012007846817141399, 0.0001237954420503229, 0.0001273923262488097, 0.00013085441605653614, 0.00013416614092420787, 0.00013731095532421023, 0.00014027139695826918, 0.0001430292468285188, 0.00014556545647792518, 0.00014786020619794726, 0.00014989302144385874, 0.00015164281649049371, 0.00015308793808799237, 0.00015420628187712282, 0.00015497540880460292, 0.0001553725014673546, 0.00015537462604697794, 0.00015495868865400553, 0.0001541016681585461, 0.0001527806743979454, 0.000150972991832532, 0.00014865631237626076, 0.0001458088227082044, 0.00014240926248021424, 0.00013843717169947922, 0.00013387289072852582, 0.00012869780766777694, 0.00012289444566704333, 0.00011644652840914205, 0.00010933926387224346, 0.00010155932977795601, 9.309507731813937e-05, 8.393668395001441e-05, 7.407623343169689e-05, 6.350783951347694e-05, 5.2227820560801774e-05, 4.023476139991544e-05, 2.7529658837011084e-05, 1.4116030797595158e-05, -1.1277033424057267e-19, -1.4809590538789053e-05, -3.03010965581052e-05, -4.645998342311941e-05, -6.32687660981901e-05, -8.070691546890885e-05, -9.875082469079643e-05, -0.00011737374734366313, -0.00013654578651767224, -0.00015623382932972163, -0.00017640153237152845, -0.00019700932898558676, -0.00021801443654112518, -0.00023937092919368297, -0.000261029606917873, -0.00028293815557844937, -0.00030504129244945943, -0.00032728054793551564, -0.0003495945711620152, -0.00037191930459812284, -0.0003941877803299576, -0.0004163304402027279, -0.00043827531044371426, -0.0004599479725584388, -0.00048127182526513934, -0.0005021682009100914, -0.0005225568311288953, -0.0005423553520813584, -0.0005614803521893919, -0.0005798469064757228, -0.0005973691586405039, -0.0006139606120996177, -0.0006295338971540332, -0.000644001760520041, -0.0006572765414603055, -0.0006692712777294219, -0.0006798990070819855, -0.0006890740478411317, -0.0006967115914449096, -0.000702728284522891, -0.0007070426363497972, -0.0007095747860148549, -0.0007102476083673537, -0.0007089864229783416, -0.0007057195180095732, -0.0007003784994594753, -0.0006928984075784683, -0.0006832184735685587, -0.000671281770337373, -0.000657036027405411, -0.0006404338637366891, -0.0006214328459464014, -0.0005999959539622068, -0.000576091930270195, -0.0005496952799148858, -0.0005207868525758386, -0.0004893539007753134, -0.00045539034181274474, -0.0004188970779068768, -0.0003798819670919329, -0.00033836046350188553, -0.00029435535543598235, -0.00024789711460471153, -0.0001990241144085303, -0.0001477827172493562, -9.422734729014337e-05, -3.842059595626779e-05, 1.9566638002288528e-05, 7.965514669194818e-05, 0.0001417573803337291, 0.00020577735267579556, 0.0002716107410378754, 0.00033914492814801633, 0.0004082589002791792, 0.00047882343642413616, 0.000550701399333775, 0.0006237471825443208, 0.0006978079327382147, 0.0007727226475253701, 0.0008483228739351034, 0.0009244330576620996, 0.0010008704848587513, 0.0010774459224194288, 0.0011539628030732274, 0.0012302196118980646, 0.0013060078490525484, 0.0013811138924211264, 0.0014553191140294075, 0.0015284003457054496, 0.00160012929700315, 0.001670274417847395, 0.0017386004328727722, 0.0018048692727461457, 0.0018688400741666555, 0.0019302699947729707, 0.001988915028050542, 0.0020445294212549925, 0.002096867887303233, 0.0021456845570355654, 0.0021907349582761526, 0.0022317746188491583, 0.002268562326207757, 0.002300858497619629, 0.002328426344320178, 0.002351032802835107, 0.002368449466302991, 0.0023804516531527042, 0.002386821433901787, 0.0023873455356806517, 0.002381817903369665, 0.0023700387682765722, 0.0023518172092735767, 0.0023269695229828358, 0.0022953213192522526, 0.0022567075211554766, 0.002210972597822547, 0.0021579712629318237, 0.002097569638863206, 0.0020296447910368443, 0.001954086124897003, 0.001870793872512877, 0.0017796827014535666, 0.001680679153650999, 0.0015737236244603992, 0.001458770246244967, 0.0013357873540371656, 0.0012047573691233993, 0.0010656777303665876, 0.0009185601375065744, 0.0007634324138052762, 0.0006003368180245161, 0.00042933132499456406, 0.0002504894800949842, 6.390033377101645e-05, -0.0001303313038079068, -0.0003320850373711437, -0.0005412247264757752, -0.0007575987838208675, -0.0009810400661081076, -0.0012113659176975489, -0.0014483786653727293, -0.001691865618340671, -0.0019415994174778461, -0.002197337569668889, -0.002458824310451746, -0.0027257895562797785, -0.002997949253767729, -0.0032750072423368692, -0.00355665385723114, -0.0038425675593316555, -0.004132415167987347, -0.004425852559506893, -0.004722523968666792, -0.005022064782679081, -0.005324100144207478, -0.0056282468140125275, -0.005934113170951605, -0.006241301074624062, -0.006549403537064791, -0.006858009845018387, -0.007166701834648848, -0.007475059013813734, -0.007782654836773872, -0.008089061826467514, -0.0083938492462039, -0.008696584962308407, -0.008996834978461266, -0.009294169023633003, -0.009588155895471573, -0.009878363460302353, -0.010164367966353893, -0.01044574473053217, -0.010722074657678604, -0.010992946103215218, -0.011257949285209179, -0.011516684666275978, -0.011768758296966553, -0.012013785541057587, -0.012251392006874084, -0.012481208890676498, -0.01270288322120905, -0.012916072271764278, -0.013120441697537899, -0.013315673917531967, -0.013501462526619434, -0.013677516020834446, -0.013843556866049767, -0.013999324291944504, -0.014144569635391235, -0.014279062859714031, -0.014402593486011028, -0.014514961279928684, -0.014615988358855247, -0.014705514535307884, -0.014783395454287529, -0.014849507249891758, -0.014903743751347065, -0.01494601834565401, -0.014976263046264648, -0.014994428493082523, 0.9850320219993591, -0.014994428493082523, -0.014976263046264648, -0.01494601834565401, -0.014903743751347065, -0.014849507249891758, -0.014783395454287529, -0.014705514535307884, -0.014615988358855247, -0.014514961279928684, -0.014402593486011028, -0.014279062859714031, -0.014144569635391235, -0.013999324291944504, -0.013843556866049767, -0.013677516020834446, -0.013501462526619434, -0.013315673917531967, -0.013120441697537899, -0.012916072271764278, -0.01270288322120905, -0.012481208890676498, -0.012251392006874084, -0.012013785541057587, -0.011768758296966553, -0.011516684666275978, -0.011257949285209179, -0.010992946103215218, -0.010722074657678604, -0.01044574473053217, -0.010164367966353893, -0.009878363460302353, -0.009588155895471573, -0.009294169023633003, -0.008996834978461266, -0.008696584962308407, -0.0083938492462039, -0.008089061826467514, -0.007782654836773872, -0.007475059013813734, -0.007166701834648848, -0.006858009845018387, -0.006549403537064791, -0.006241301074624062, -0.005934113170951605, -0.0056282468140125275, -0.005324100144207478, -0.005022064782679081, -0.004722523968666792, -0.004425852559506893, -0.004132415167987347, -0.0038425675593316555, -0.00355665385723114, -0.0032750072423368692, -0.002997949253767729, -0.0027257895562797785, -0.002458824310451746, -0.002197337569668889, -0.0019415994174778461, -0.001691865618340671, -0.0014483786653727293, -0.0012113659176975489, -0.0009810400661081076, -0.0007575987838208675, -0.0005412247264757752, -0.0003320850373711437, -0.0001303313038079068, 6.390033377101645e-05, 0.0002504894800949842, 0.00042933132499456406, 0.0006003368180245161, 0.0007634324138052762, 0.0009185601375065744, 0.0010656777303665876, 0.0012047573691233993, 0.0013357873540371656, 0.001458770246244967, 0.0015737236244603992, 0.001680679153650999, 0.0017796827014535666, 0.001870793872512877, 0.001954086124897003, 0.0020296447910368443, 0.002097569638863206, 0.0021579712629318237, 0.002210972597822547, 0.0022567075211554766, 0.0022953213192522526, 0.0023269695229828358, 0.0023518172092735767, 0.0023700387682765722, 0.002381817903369665, 0.0023873455356806517, 0.002386821433901787, 0.0023804516531527042, 0.002368449466302991, 0.002351032802835107, 0.002328426344320178, 0.002300858497619629, 0.002268562326207757, 0.0022317746188491583, 0.0021907349582761526, 0.0021456845570355654, 0.002096867887303233, 0.0020445294212549925, 0.001988915028050542, 0.0019302699947729707, 0.0018688400741666555, 0.0018048692727461457, 0.0017386004328727722, 0.001670274417847395, 0.00160012929700315, 0.0015284003457054496, 0.0014553191140294075, 0.0013811138924211264, 0.0013060078490525484, 0.0012302196118980646, 0.0011539628030732274, 0.0010774459224194288, 0.0010008704848587513, 0.0009244330576620996, 0.0008483228739351034, 0.0007727226475253701, 0.0006978079327382147, 0.0006237471825443208, 0.000550701399333775, 0.00047882343642413616, 0.0004082589002791792, 0.00033914492814801633, 0.0002716107410378754, 0.00020577735267579556, 0.0001417573803337291, 7.965514669194818e-05, 1.9566638002288528e-05, -3.842059595626779e-05, -9.422734729014337e-05, -0.0001477827172493562, -0.0001990241144085303, -0.00024789711460471153, -0.00029435535543598235, -0.00033836046350188553, -0.0003798819670919329, -0.0004188970779068768, -0.00045539034181274474, -0.0004893539007753134, -0.0005207868525758386, -0.0005496952799148858, -0.000576091930270195, -0.0005999959539622068, -0.0006214328459464014, -0.0006404338637366891, -0.000657036027405411, -0.000671281770337373, -0.0006832184735685587, -0.0006928984075784683, -0.0007003784994594753, -0.0007057195180095732, -0.0007089864229783416, -0.0007102476083673537, -0.0007095747860148549, -0.0007070426363497972, -0.000702728284522891, -0.0006967115914449096, -0.0006890740478411317, -0.0006798990070819855, -0.0006692712777294219, -0.0006572765414603055, -0.000644001760520041, -0.0006295338971540332, -0.0006139606120996177, -0.0005973691586405039, -0.0005798469064757228, -0.0005614803521893919, -0.0005423553520813584, -0.0005225568311288953, -0.0005021682009100914, -0.00048127182526513934, -0.0004599479725584388, -0.00043827531044371426, -0.0004163304402027279, -0.0003941877803299576, -0.00037191930459812284, -0.0003495945711620152, -0.00032728054793551564, -0.00030504129244945943, -0.00028293815557844937, -0.000261029606917873, -0.00023937092919368297, -0.00021801443654112518, -0.00019700932898558676, -0.00017640153237152845, -0.00015623382932972163, -0.00013654578651767224, -0.00011737374734366313, -9.875082469079643e-05, -8.070691546890885e-05, -6.32687660981901e-05, -4.645998342311941e-05, -3.03010965581052e-05, -1.4809590538789053e-05, -1.1277033424057267e-19, 1.4116030797595158e-05, 2.7529658837011084e-05, 4.023476139991544e-05, 5.2227820560801774e-05, 6.350783951347694e-05, 7.407623343169689e-05, 8.393668395001441e-05, 9.309507731813937e-05, 0.00010155932977795601, 0.00010933926387224346, 0.00011644652840914205, 0.00012289444566704333, 0.00012869780766777694, 0.00013387289072852582, 0.00013843717169947922, 0.00014240926248021424, 0.0001458088227082044, 0.00014865631237626076, 0.000150972991832532, 0.0001527806743979454, 0.0001541016681585461, 0.00015495868865400553, 0.00015537462604697794, 0.0001553725014673546, 0.00015497540880460292, 0.00015420628187712282, 0.00015308793808799237, 0.00015164281649049371, 0.00014989302144385874, 0.00014786020619794726, 0.00014556545647792518, 0.0001430292468285188, 0.00014027139695826918, 0.00013731095532421023, 0.00013416614092420787, 0.00013085441605653614, 0.0001273923262488097, 0.0001237954420503229, 0.00012007846817141399, 0.00011625513434410095, 0.00011233818077016622, 0.00010833935084519908, 0.00010426943481434137, 0.00010013821156462654, 9.595452866051346e-05, 9.172626596409827e-05, 8.746036473894492e-05, 8.3162885857746e-05, 7.88389952504076e-05, 7.449306576745585e-05, 7.012864807620645e-05, 6.574857980012894e-05, 6.135496369097382e-05, 5.694930223398842e-05, 5.253248309600167e-05, 4.810490281670354e-05, 4.3666452256729826e-05, 3.921664392692037e-05, 3.475465564406477e-05], 1)
        self.fft_filter_xxx_0.declare_sample_delay(0)
        self.correctiq_correctiq_0 = correctiq.correctiq()
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 64)
        self.blocks_pdu_to_tagged_stream_1 = blocks.pdu_to_tagged_stream(blocks.complex_t, 'packet_len')
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_multiply_const_xx_0 = blocks.multiply_const_cc(gain, 1)
        self.blocks_moving_average_xx_1 = blocks.moving_average_cc(window_size, 1, 4000, 1)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(window_size  + 16, 1, 4000, 1)
        self.blocks_divide_xx_0 = blocks.divide_ff(1)
        self.blocks_delay_0_0 = blocks.delay(gr.sizeof_gr_complex*1, 16)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, sync_length)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.ieee802_11_decode_mac_0, 'out'), (self.ieee802_11_parse_mac_0, 'in'))
        self.msg_connect((self.ieee802_11_frame_equalizer_0, 'symbols'), (self.blocks_pdu_to_tagged_stream_1, 'pdus'))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_delay_0, 0), (self.ieee802_11_sync_long_0, 1))
        self.connect((self.blocks_delay_0_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_delay_0_0, 0), (self.ieee802_11_sync_short_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.ieee802_11_sync_short_0, 2))
        self.connect((self.blocks_divide_xx_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_moving_average_xx_1, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.blocks_moving_average_xx_1, 0), (self.ieee802_11_sync_short_0, 1))
        self.connect((self.blocks_multiply_const_xx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.blocks_multiply_const_xx_0, 0), (self.blocks_delay_0_0, 0))
        self.connect((self.blocks_multiply_const_xx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_moving_average_xx_1, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_1, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.correctiq_correctiq_0, 0), (self.blocks_multiply_const_xx_0, 0))
        self.connect((self.fft_filter_xxx_0, 0), (self.correctiq_correctiq_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.ieee802_11_frame_equalizer_0, 0))
        self.connect((self.ieee802_11_frame_equalizer_0, 0), (self.ieee802_11_decode_mac_0, 0))
        self.connect((self.ieee802_11_sync_long_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.ieee802_11_sync_long_0, 0))
        self.connect((self.soapy_limesdr_source_0, 0), (self.fft_filter_xxx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "wifi_rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_window_size(self):
        return self.window_size

    def set_window_size(self, window_size):
        self.window_size = window_size
        self.blocks_moving_average_xx_0.set_length_and_scale(self.window_size  + 16, 1)
        self.blocks_moving_average_xx_1.set_length_and_scale(self.window_size, 1)

    def get_sync_length(self):
        return self.sync_length

    def set_sync_length(self, sync_length):
        self.sync_length = sync_length
        self.blocks_delay_0.set_dly(self.sync_length)

    def get_sens(self):
        return self.sens

    def set_sens(self, sens):
        self.sens = sens

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self._samp_rate_callback(self.samp_rate)
        self.ieee802_11_frame_equalizer_0.set_bandwidth(self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.soapy_limesdr_source_0.set_sample_rate(0, self.samp_rate)

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain
        self.soapy_limesdr_source_0.set_gain(0, min(max(self.rf_gain, -12.0), 61.0))

    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset
        self._lo_offset_callback(self.lo_offset)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.blocks_multiply_const_xx_0.set_k(self.gain)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.ieee802_11_frame_equalizer_0.set_frequency(self.freq)
        self.soapy_limesdr_source_0.set_frequency(0, self.freq)

    def get_chan_est(self):
        return self.chan_est

    def set_chan_est(self, chan_est):
        self.chan_est = chan_est
        self._chan_est_callback(self.chan_est)
        self.ieee802_11_frame_equalizer_0.set_algorithm(ieee802_11.Equalizer(self.chan_est))




def main(top_block_cls=wifi_rx, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
