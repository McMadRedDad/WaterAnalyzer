#include "resulttab.hpp"
#include "ui_resulttab.h"

ResultTab::ResultTab(QWidget *parent) : QWidget(parent), ui(new Ui::ResultTab) {
    ui->setupUi(this);
    ui->tb_stats->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    ui->tb_stats->verticalHeader()->setSectionResizeMode(QHeaderView::Stretch);
}

ResultTab::~ResultTab() {
    delete ui;
}

void ResultTab::set_preview(QPixmap image) {
    ui->lbl_preview->clear();
    ui->lbl_preview->setPixmap(image);
}

uint ResultTab::get_preview_width() {
    return ui->lbl_preview->width() - 2;
}

uint ResultTab::get_preview_height() {
    return ui->lbl_preview->height() - 2;
}

void ResultTab::set_caption(QString caption) {
    ui->lbl_caption->setText(caption);
}

void ResultTab::set_statistics(double min, double max, double mean, double stdev, QString ph_unit) {
    QStringList stats = {QString::number(min), QString::number(max), QString::number(mean), QString::number(stdev), ph_unit};
    for (int i = 0; i < ui->tb_stats->rowCount() && i < stats.length(); i++) {
        QTableWidgetItem *prev = ui->tb_stats->takeItem(i, 1);
        delete prev;
        QTableWidgetItem *it = new QTableWidgetItem(stats[i]);
        ui->tb_stats->setItem(i, 1, it);
    }
}

void ResultTab::hide_export_button(QString type) {
    if (type == "index") {
        QGridLayout *lyt = qobject_cast<QGridLayout *>(layout());
        ui->pb_export_index->hide();
        lyt->removeWidget(ui->pb_export_index);
        lyt->removeWidget(ui->widget_preview);
        lyt->addWidget(ui->widget_preview, 0, 0, 2, 1);
    } else if (type == "description") {
        QGridLayout *lyt = qobject_cast<QGridLayout *>(layout());
        ui->pb_export_text->hide();
        lyt->removeWidget(ui->pb_export_text);
        lyt->removeWidget(ui->widget_text);
        lyt->addWidget(ui->widget_text, 0, 1, 2, 1);
    }
}

void ResultTab::hide_stats() {
    ui->tb_stats->hide();
    ui->widget_text->layout()->removeWidget(ui->tb_stats);
}

void ResultTab::on_pb_refresh_clicked() {
    emit refresh_preview();
}

void ResultTab::on_pb_export_index_clicked() {
    emit export_index();
}

void ResultTab::on_pb_export_text_clicked() {
    QString description;
    // text from table + text from label
    emit export_text(description);
}
