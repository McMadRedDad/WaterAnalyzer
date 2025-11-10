#include "processpage.hpp"
#include "ui_processpage.h"
#include <QHeaderView>

ProcessPage::ProcessPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ProcessPage) {
    ui->setupUi(this);
    tb = new QTableWidget(9, 2);
    tb->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    tb->verticalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    QStringList names = {"Спутник",
                         "Открыто файлов",
                         "Каналы",
                         "Ширина",
                         "Высота",
                         "Проекция",
                         "Единицы измерения",
                         "Координаты привязки",
                         "Размер пикселя"};
    for (int i = 0; i < names.length(); i++) {
        QTableWidgetItem *it = new QTableWidgetItem(names[i]);
        tb->setItem(i, 0, it);
    }

    ui->lbl_warn_water->setPixmap(QPixmap(":/icons/warning.png").scaledToWidth(24));
    ui->lbl_warn_tss->setPixmap(QPixmap(":/icons/warning.png").scaledToWidth(24));
    ui->lbl_warn_chloro->setPixmap(QPixmap(":/icons/warning.png").scaledToWidth(24));
    ui->lbl_warn_cdom->setPixmap(QPixmap(":/icons/warning.png").scaledToWidth(24));
    ui->lbl_warn_temp->setPixmap(QPixmap(":/icons/warning.png").scaledToWidth(24));
    ui->lbl_warn_water->hide();
    ui->lbl_warn_tss->hide();
    ui->lbl_warn_chloro->hide();
    ui->lbl_warn_cdom->hide();
    ui->lbl_warn_temp->hide();
    on_combo_water_currentTextChanged(ui->combo_water->currentText());
    on_combo_tss_currentTextChanged(ui->combo_tss->currentText());
    on_combo_chloro_currentTextChanged(ui->combo_chloro->currentText());
    on_combo_cdom_currentTextChanged(ui->combo_cdom->currentText());
    on_combo_temp_currentTextChanged(ui->combo_temp->currentText());
}

ProcessPage::~ProcessPage() {
    delete ui;
    delete tb;
}

void ProcessPage::set_preview(QPixmap image) {
    ui->lbl_preview->clear();
    ui->lbl_preview->setPixmap(image);
}

void ProcessPage::clear_preview() {
    ui->lbl_preview->clear();
}

void ProcessPage::fill_metadata(QStringList metadata) {
    for (int i = 0; i < tb->rowCount() && i < metadata.length(); i++) {
        QTableWidgetItem *prev = tb->takeItem(i, 1);
        delete prev;
        QTableWidgetItem *it = new QTableWidgetItem(metadata[i]);
        tb->setItem(i, 1, it);
    }
    tb->show();
}

void ProcessPage::show_temperature_toa(bool yes) {
    if (yes) {
        for (int i = 0; i < ui->combo_temp->count(); i++) {
            if (ui->combo_temp->itemText(i).contains("Атмосфера")) {
                return;
            }
        }
        ui->combo_temp->addItem("Атмосфера");
    } else {
        for (int i = 0; i < ui->combo_temp->count(); i++) {
            if (ui->combo_temp->itemText(i).contains("Атмосфера")) {
                ui->combo_temp->removeItem(i);
                return;
            }
        }
    }
}

void ProcessPage::on_pb_refresh_clicked() {
    clear_preview();
    emit preview(ui->lbl_preview->width() - 2, ui->lbl_preview->height() - 2);
}

void ProcessPage::on_pb_meta_clicked() {
    emit require_metadata();
}

void ProcessPage::on_pb_go_clicked() {
    QStringList indices;
    indices.append(ui->combo_water->currentText());
    indices.append(ui->combo_tss->currentText());
    indices.append(ui->combo_chloro->currentText());
    indices.append(ui->combo_cdom->currentText());
    if (ui->combo_temp->currentText().contains("Земля")) {
        indices.append("ls_temperature_landsat");
    } else {
        indices.append("toa_temperature_landsat");
    }
    emit this->indices(indices);
}

void ProcessPage::on_combo_water_currentTextChanged(const QString &arg1) {
    QString tip;
    QString index = arg1.toLower();
    if (index == "wi2015") {
        tip = "Пороговое значение для классификации будет определено автоматически методом Оцу. Результат может быть неточным.";
        ui->lbl_warn_water->show();
    } else if (index == "andwi") {
        tip = "Пороговое значение для классификации будет определено автоматически методом Оцу. Результат может быть неточным.";
        ui->lbl_warn_water->show();
    } else {
        tip = "";
        ui->lbl_warn_water->hide();
    }
    ui->lbl_warn_water->setToolTip(tip);
}

void ProcessPage::on_combo_chloro_currentTextChanged(const QString &arg1) {
    QString tip;
    QString index = arg1.toLower();
    if (index == "oc3_concentration") {
        tip = "Концентрация хлорофилла будет рассчитана исходя из эмпирического полинома. Результат необходимо валидировать.";
        ui->lbl_warn_chloro->show();
    } else {
        tip = "";
        ui->lbl_warn_chloro->hide();
    }
    ui->lbl_warn_chloro->setToolTip(tip);
}

void ProcessPage::on_combo_tss_currentTextChanged(const QString &arg1) {
    QString tip;
    QString index = arg1.toLower();
    if (index == "nsmi") {
        tip = "";
        ui->lbl_warn_tss->hide();
    } else {
        tip = "";
        ui->lbl_warn_tss->hide();
    }
    ui->lbl_warn_tss->setToolTip(tip);
}

void ProcessPage::on_combo_cdom_currentTextChanged(const QString &arg1) {
    QString tip;
    QString index = arg1.toLower();
    if (index == "cdom_ndwi") {
        tip = "Концентрация цветных органических частиц будет рассчитана исходя из эмпирического полинома. Результат необходимо "
              "валидировать.";
        ui->lbl_warn_cdom->show();
    } else {
        tip = "";
        ui->lbl_warn_cdom->hide();
    }
    ui->lbl_warn_cdom->setToolTip(tip);
}

void ProcessPage::on_combo_temp_currentTextChanged(const QString &arg1) {
    QString tip;
    QString index = arg1.toLower();
    if (index == "toa_temperature_landsat") {
        tip = "";
        ui->lbl_warn_temp->hide();
    } else if (index == "ls_temperature_landsat") {
        tip = "";
        ui->lbl_warn_temp->hide();
    } else {
        tip = "";
        ui->lbl_warn_temp->hide();
    }
    ui->lbl_warn_temp->setToolTip(tip);
}
