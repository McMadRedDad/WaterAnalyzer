#include "uibuilder.hpp"

ClickableQWidget* UiBuilder::build_import_page(QWidget* parent_with_layout) {
    if (!parent_with_layout->layout()) {
        return nullptr;
    }

    ClickableQWidget* w = new ClickableQWidget(parent_with_layout);
    QVBoxLayout*      lyt = new QVBoxLayout();
    QLabel*           capt = new QLabel();

    capt->setText("Нажмите, чтобы открыть директорию со снимком.");
    capt->setAlignment(Qt::AlignCenter);

    lyt->addWidget(capt);

    w->setLayout(lyt);
    w->set_clickable(true);

    return w;
}

ClickableQWidget* UiBuilder::build_selection_page(QWidget* parent_with_layout) {
    ClickableQWidget* w = new ClickableQWidget(parent_with_layout);
    QHBoxLayout*      lyt = new QHBoxLayout();
    ClickableQWidget* preview = new ClickableQWidget();
    QVBoxLayout*      vlyt = new QVBoxLayout();
    QHBoxLayout*      hlyt_water = new QHBoxLayout();
    QHBoxLayout*      hlyt_chlorophyll = new QHBoxLayout();
    QHBoxLayout*      hlyt_cdom = new QHBoxLayout();
    QHBoxLayout*      hlyt_tss = new QHBoxLayout();
    QHBoxLayout*      hlyt_temperature = new QHBoxLayout();
    QLabel*           lb_water = new QLabel();
    QLabel*           lb_chlorophyll = new QLabel();
    QLabel*           lb_cdom = new QLabel();
    QLabel*           lb_tss = new QLabel();
    QLabel*           lb_temperature = new QLabel();
    QComboBox*        cb_water = new QComboBox();
    QComboBox*        cb_chlorophyll = new QComboBox();
    QComboBox*        cb_cdom = new QComboBox();
    QComboBox*        cb_tss = new QComboBox();
    QCheckBox*        ckbx_temperature = new QCheckBox();
    QPushButton*      pb_go = new QPushButton();

    w->set_clickable(false);
    // preview...
    lb_water->setText("water");
    lb_chlorophyll->setText("chlorophyll-a");
    lb_cdom->setText("cdom");
    lb_tss->setText("tss");
    lb_temperature->setText("temperature");
    cb_water->addItems({"1", "2"});
    cb_chlorophyll->addItems({"1", "2"});
    cb_cdom->addItems({"1", "2"});
    cb_tss->addItems({"1", "2"});
    pb_go->setText("go!");

    hlyt_water->addWidget(lb_water);
    hlyt_water->addWidget(cb_water);
    hlyt_chlorophyll->addWidget(lb_chlorophyll);
    hlyt_chlorophyll->addWidget(cb_chlorophyll);
    hlyt_cdom->addWidget(lb_cdom);
    hlyt_cdom->addWidget(cb_cdom);
    hlyt_tss->addWidget(lb_tss);
    hlyt_tss->addWidget(cb_tss);
    hlyt_temperature->addWidget(lb_temperature);
    hlyt_temperature->addWidget(ckbx_temperature);
    vlyt->addLayout(hlyt_water);
    vlyt->addLayout(hlyt_chlorophyll);
    vlyt->addLayout(hlyt_cdom);
    vlyt->addLayout(hlyt_tss);
    vlyt->addLayout(hlyt_temperature);
    vlyt->addWidget(pb_go);
    lyt->addWidget(preview);
    lyt->addLayout(vlyt);

    w->setLayout(lyt);

    return w;
}

ClickableQWidget* UiBuilder::build_results_page(QWidget* parent_with_layout) {
    ClickableQWidget* w = new ClickableQWidget(parent_with_layout);
    QVBoxLayout*      lyt = new QVBoxLayout();
    QTabWidget*       tabs = new QTabWidget();
    QWidget*          tab_overview = new QWidget();
    QWidget*          tab_water = new QWidget();
    QWidget*          tab_chlorophyll = new QWidget();
    QWidget*          tab_cdom = new QWidget();
    QWidget*          tab_tss = new QWidget();
    QWidget*          tab_temperature = new QWidget();
    QHBoxLayout*      hlyt_overview = new QHBoxLayout();
    QHBoxLayout*      hlyt_water = new QHBoxLayout();
    QHBoxLayout*      hlyt_chlorophyll = new QHBoxLayout();
    QHBoxLayout*      hlyt_cdom = new QHBoxLayout();
    QHBoxLayout*      hlyt_tss = new QHBoxLayout();
    QHBoxLayout*      hlyt_temperature = new QHBoxLayout();
    ClickableQWidget* preview_overview = new ClickableQWidget();
    ClickableQWidget* preview_water = new ClickableQWidget();
    ClickableQWidget* preview_chlorophyll = new ClickableQWidget();
    ClickableQWidget* preview_cdom = new ClickableQWidget();
    ClickableQWidget* preview_tss = new ClickableQWidget();
    ClickableQWidget* preview_temperature = new ClickableQWidget();
    QVBoxLayout*      vlyt_overview = new QVBoxLayout();
    QVBoxLayout*      vlyt_water = new QVBoxLayout();
    QVBoxLayout*      vlyt_chlorophyll = new QVBoxLayout();
    QVBoxLayout*      vlyt_cdom = new QVBoxLayout();
    QVBoxLayout*      vlyt_tss = new QVBoxLayout();
    QVBoxLayout*      vlyt_temperature = new QVBoxLayout();
    QLabel*           lb_overview = new QLabel();
    QLabel*           lb_water = new QLabel();
    QLabel*           lb_chlorophyll = new QLabel();
    QLabel*           lb_cdom = new QLabel();
    QLabel*           lb_tss = new QLabel();
    QLabel*           lb_temperature = new QLabel();
    QPushButton*      pb_export_overview = new QPushButton();
    QPushButton*      pb_export_water = new QPushButton();
    QPushButton*      pb_export_chlorophyll = new QPushButton();
    QPushButton*      pb_export_cdom = new QPushButton();
    QPushButton*      pb_export_tss = new QPushButton();
    QPushButton*      pb_export_temperature = new QPushButton();

    w->set_clickable(false);
    tabs->addTab(tab_overview, "overview");
    tabs->addTab(tab_water, "water");
    tabs->addTab(tab_chlorophyll, "chlorophyll-a");
    tabs->addTab(tab_cdom, "cdom");
    tabs->addTab(tab_tss, "tss");
    tabs->addTab(tab_temperature, "temperature");
    // previews...
    lb_overview->setText("long overview...\nnextline");
    lb_water->setText("water");
    lb_chlorophyll->setText("chlorophyll-a");
    lb_cdom->setText("cdom");
    lb_tss->setText("tss");
    lb_temperature->setText("temperature");
    pb_export_overview->setText("export");
    pb_export_water->setText("export");
    pb_export_chlorophyll->setText("export");
    pb_export_cdom->setText("export");
    pb_export_tss->setText("export");
    pb_export_temperature->setText("export");

    vlyt_overview->addWidget(lb_overview);
    vlyt_overview->addWidget(pb_export_overview);
    vlyt_water->addWidget(lb_water);
    vlyt_water->addWidget(pb_export_water);
    vlyt_chlorophyll->addWidget(lb_chlorophyll);
    vlyt_chlorophyll->addWidget(pb_export_chlorophyll);
    vlyt_cdom->addWidget(lb_cdom);
    vlyt_cdom->addWidget(pb_export_cdom);
    vlyt_tss->addWidget(lb_tss);
    vlyt_tss->addWidget(pb_export_tss);
    vlyt_temperature->addWidget(lb_temperature);
    vlyt_temperature->addWidget(pb_export_temperature);
    hlyt_overview->addWidget(preview_overview);
    hlyt_overview->addLayout(vlyt_overview);
    hlyt_water->addWidget(preview_water);
    hlyt_water->addLayout(vlyt_water);
    hlyt_chlorophyll->addWidget(preview_chlorophyll);
    hlyt_chlorophyll->addLayout(vlyt_chlorophyll);
    hlyt_cdom->addWidget(preview_cdom);
    hlyt_cdom->addLayout(vlyt_cdom);
    hlyt_tss->addWidget(preview_tss);
    hlyt_tss->addLayout(vlyt_tss);
    hlyt_temperature->addWidget(preview_temperature);
    hlyt_temperature->addLayout(vlyt_temperature);
    lyt->addWidget(tabs);

    tab_overview->setLayout(hlyt_overview);
    tab_water->setLayout(hlyt_water);
    tab_chlorophyll->setLayout(hlyt_chlorophyll);
    tab_cdom->setLayout(hlyt_cdom);
    tab_tss->setLayout(hlyt_tss);
    tab_temperature->setLayout(hlyt_temperature);

    w->setLayout(lyt);

    return w;
}
