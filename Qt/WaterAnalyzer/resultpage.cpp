#include "resultpage.hpp"
#include "ui_resultpage.h"

ResultPage::ResultPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ResultPage) {
    ui->setupUi(this);
    summary = new ResultTab();
    water = new ResultTab();
    chloro = new ResultTab();
    tss = new ResultTab();
    cdom = new ResultTab();
    temp = new ResultTab();

    connect(summary, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);
    connect(water, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);
    connect(chloro, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);
    connect(tss, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);
    connect(cdom, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);
    connect(temp, &ResultTab::refresh_preview, this, &ResultPage::update_all_previews);

    connect(summary, &ResultTab::export_index, [this]() { emit export_index("summary"); });
    connect(water, &ResultTab::export_index, [this]() { emit export_index("water"); });
    connect(chloro, &ResultTab::export_index, [this]() { emit export_index("chloro"); });
    connect(tss, &ResultTab::export_index, [this]() { emit export_index("tss"); });
    connect(cdom, &ResultTab::export_index, [this]() { emit export_index("cdom"); });
    connect(temp, &ResultTab::export_index, [this]() { emit export_index("temp"); });

    connect(summary, &ResultTab::export_text, this, &ResultPage::export_text);
    connect(water, &ResultTab::export_text, this, &ResultPage::export_text);
    connect(chloro, &ResultTab::export_text, this, &ResultPage::export_text);
    connect(tss, &ResultTab::export_text, this, &ResultPage::export_text);
    connect(cdom, &ResultTab::export_text, this, &ResultPage::export_text);
    connect(temp, &ResultTab::export_text, this, &ResultPage::export_text);

    ui->tab_summary->layout()->addWidget(summary);
    ui->tab_water->layout()->addWidget(water);
    ui->tab_chloro->layout()->addWidget(chloro);
    ui->tab_tss->layout()->addWidget(tss);
    ui->tab_cdom->layout()->addWidget(cdom);
    ui->tab_temp->layout()->addWidget(temp);
    summary->set_caption("Итог");
    summary->hide_stats();
}

ResultPage::~ResultPage() {
    delete ui;
    delete summary;
    delete water;
    delete chloro;
    delete tss;
    delete cdom;
    delete temp;
}

void ResultPage::set_preview(QString page, QPixmap image) {
    if (page == "summary") {
        summary->set_preview(image);
    } else if (page == "water") {
        water->set_preview(image);
    } else if (page == "chloro") {
        chloro->set_preview(image);
    } else if (page == "tss") {
        tss->set_preview(image);
    } else if (page == "cdom") {
        cdom->set_preview(image);
    } else if (page == "temp") {
        temp->set_preview(image);
    }
}

uint ResultPage::get_preview_width() {
    return water->get_preview_width();
}

uint ResultPage::get_preview_height() {
    return water->get_preview_height();
}

void ResultPage::set_caption(QString page, QString caption) {
    if (page == "summary") {
        summary->set_caption(caption);
    } else if (page == "water") {
        water->set_caption(caption);
    } else if (page == "chloro") {
        chloro->set_caption(caption);
    } else if (page == "tss") {
        tss->set_caption(caption);
    } else if (page == "cdom") {
        cdom->set_caption(caption);
    } else if (page == "temp") {
        temp->set_caption(caption);
    }
}

void ResultPage::set_statistics(QString page, double min, double max, double mean, double stdev, QString ph_unit) {
    if (page == "summary") {
        summary->set_statistics(min, max, mean, stdev, ph_unit);
    } else if (page == "water") {
        water->set_statistics(min, max, mean, stdev, ph_unit);
    } else if (page == "chloro") {
        chloro->set_statistics(min, max, mean, stdev, ph_unit);
    } else if (page == "tss") {
        tss->set_statistics(min, max, mean, stdev, ph_unit);
    } else if (page == "cdom") {
        cdom->set_statistics(min, max, mean, stdev, ph_unit);
    } else if (page == "temp") {
        temp->set_statistics(min, max, mean, stdev, ph_unit);
    }
}

void ResultPage::set_description(QString page, QString text) {
    if (page == "summary") {
        summary->set_description(text);
    } else if (page == "water") {
        water->set_description(text);
    } else if (page == "chloro") {
        chloro->set_description(text);
    } else if (page == "tss") {
        tss->set_description(text);
    } else if (page == "cdom") {
        cdom->set_description(text);
    } else if (page == "temp") {
        temp->set_description(text);
    }
}
